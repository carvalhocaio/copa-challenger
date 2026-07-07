"""Backtest do modelo preditivo — Missão 04.

Treina força ofensiva/defensiva só com os jogos de 2018 e avalia nos 64
jogos de 2022 que têm ranking FIFA real. Sem vazamento: a força usada pra
prever um jogo de 2022 nunca viu resultados de 2022. É um único fold (não
dá pra fazer k-fold sem ranking de 2018) — alta variância, leia os números
como indício, não validação robusta.
"""

from __future__ import annotations

import math

import duckdb

from copa_challenger.config import DUCKDB_PATH
from copa_challenger.predict import features, model


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def _predicted_label(probs: tuple[float, float, float]) -> str:
    prob_home, prob_draw, prob_away = probs
    labeled = {"home_win": prob_home, "draw": prob_draw, "away_win": prob_away}
    return max(labeled, key=labeled.get)


def _log_loss(actual_labels: list[str], probs: list[tuple[float, float, float]]) -> float:
    eps = 1e-12
    total = 0.0
    for label, (p_home, p_draw, p_away) in zip(actual_labels, probs, strict=True):
        p = {"home_win": p_home, "draw": p_draw, "away_win": p_away}[label]
        total += -math.log(max(p, eps))
    return total / len(actual_labels)


def run_backtest() -> None:
    con = _con()

    rankings_2022 = features.team_rankings_2022(con)
    feats = features.team_features(con, rankings_2022, years=[2018])
    fit = model.fit_fallback(feats)
    feats_full = model.apply_fallback(feats, fit)
    league_avg = features.league_average_goals(con, years=[2018])

    strength = {
        row["team"]: (row["attack"], row["defense"]) for row in feats_full.iter_rows(named=True)
    }
    rank_lookup = {row["team"]: row["rank"] for row in rankings_2022.iter_rows(named=True)}

    matches = con.sql("""
        SELECT home_team, away_team, result_regulation
        FROM mart.int_match_stages
        WHERE year = 2022
    """).pl()

    actuals: list[str] = []
    model_probs: list[tuple[float, float, float]] = []
    model_preds: list[str] = []
    favorite_preds: list[str] = []

    for row in matches.iter_rows(named=True):
        home, away, actual = row["home_team"], row["away_team"], row["result_regulation"]
        attack_home, defense_home = strength[home]
        attack_away, defense_away = strength[away]

        mu_home = model.expected_goals(attack_home, defense_away, league_avg)
        mu_away = model.expected_goals(attack_away, defense_home, league_avg)
        probs = model.match_outcome_probs(mu_home, mu_away)

        actuals.append(actual)
        model_probs.append(probs)
        model_preds.append(_predicted_label(probs))
        favorite_preds.append("home_win" if rank_lookup[home] < rank_lookup[away] else "away_win")

    n = len(actuals)
    model_accuracy = sum(p == a for p, a in zip(model_preds, actuals, strict=True)) / n
    model_log_loss = _log_loss(actuals, model_probs)
    favorite_accuracy = sum(p == a for p, a in zip(favorite_preds, actuals, strict=True)) / n

    # baseline de frequência ingênua: distribuição empírica de 2018 (treino),
    # aplicada como probabilidade fixa a todo jogo de 2022.
    train_results = con.sql("""
        SELECT result_regulation FROM mart.int_match_stages WHERE year = 2018
    """).pl()
    n_train = train_results.height
    naive_probs = (
        (train_results["result_regulation"] == "home_win").sum() / n_train,
        (train_results["result_regulation"] == "draw").sum() / n_train,
        (train_results["result_regulation"] == "away_win").sum() / n_train,
    )
    naive_pred = _predicted_label(naive_probs)
    naive_accuracy = sum(a == naive_pred for a in actuals) / n
    naive_log_loss = _log_loss(actuals, [naive_probs] * n)

    con.close()

    print(f"\nBacktest — treino: 2018 ({n_train} jogos) · teste: 2022 ({n} jogos com ranking real)")
    print("1 único fold: sem ranking de 2018 não dá pra fazer k-fold.")
    print("Leia os números como indício, não validação robusta.\n")
    print(f"{'':<30}{'accuracy':>10}{'log-loss':>10}")
    print(f"{'modelo (Poisson attack/def)':<30}{model_accuracy:>10.1%}{model_log_loss:>10.3f}")
    print(f"{'baseline: freq. ingênua 2018':<30}{naive_accuracy:>10.1%}{naive_log_loss:>10.3f}")
    print(f"{'baseline: favorito do ranking':<30}{favorite_accuracy:>10.1%}{'n/a':>10}")
