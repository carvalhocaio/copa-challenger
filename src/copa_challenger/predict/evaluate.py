"""Backtest do modelo preditivo — Missão 04.

Treina força ofensiva/defensiva só com os jogos de 2018 e avalia nos 64
jogos de 2022 que têm ranking FIFA real. Sem vazamento: a força usada pra
prever um jogo de 2022 nunca viu resultados de 2022. É um único fold (não
dá pra fazer k-fold sem ranking de 2018) — alta variância, leia os números
como indício, não validação robusta.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import duckdb
import numpy as np

from copa_challenger.config import DUCKDB_PATH
from copa_challenger.predict import features, model


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def _predicted_label(probs: tuple[float, float, float]) -> str:
    prob_home, prob_draw, prob_away = probs
    labeled = {"home_win": prob_home, "draw": prob_draw, "away_win": prob_away}
    return max(labeled, key=labeled.get)


def _log_loss_terms(
    actual_labels: list[str], probs: list[tuple[float, float, float]]
) -> list[float]:
    """-log(prob atribuída ao resultado real) por jogo. A média é o log-loss."""
    eps = 1e-12
    terms = []
    for label, (p_home, p_draw, p_away) in zip(actual_labels, probs, strict=True):
        p = {"home_win": p_home, "draw": p_draw, "away_win": p_away}[label]
        terms.append(-math.log(max(p, eps)))
    return terms


def _log_loss(actual_labels: list[str], probs: list[tuple[float, float, float]]) -> float:
    terms = _log_loss_terms(actual_labels, probs)
    return sum(terms) / len(terms)


def bootstrap_cis(
    per_game_metrics: Mapping[str, Sequence[float]],
    *,
    n_resamples: int = 1000,
    seed: int = 12345,
    percentiles: tuple[float, float] = (5.0, 95.0),
) -> dict[str, tuple[float, float]]:
    """Bootstrap não-paramétrico do IC percentil da média de cada métrica.

    Cada métrica é dada como um valor por jogo cuja média é a métrica agregada
    (acurácia = 1/0 por acerto; log-loss = termo -log por jogo). A cada
    reamostragem, os mesmos índices sorteados com reposição são aplicados a
    todas as métricas, tornando os intervalos conjuntamente consistentes.
    Determinístico dado `seed`.
    """
    rng = np.random.default_rng(seed)
    arrays = {name: np.asarray(vals, dtype=float) for name, vals in per_game_metrics.items()}
    n = len(next(iter(arrays.values())))
    means = {name: np.empty(n_resamples) for name in arrays}
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        for name, arr in arrays.items():
            means[name][b] = arr[idx].mean()
    return {
        name: (float(np.percentile(m, percentiles[0])), float(np.percentile(m, percentiles[1])))
        for name, m in means.items()
    }


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

    con.close()

    # métricas por jogo (a média de cada array é a métrica agregada) — base do bootstrap.
    model_correct = [float(p == a) for p, a in zip(model_preds, actuals, strict=True)]
    favorite_correct = [float(p == a) for p, a in zip(favorite_preds, actuals, strict=True)]
    naive_correct = [float(naive_pred == a) for a in actuals]
    model_ll_terms = _log_loss_terms(actuals, model_probs)
    naive_ll_terms = _log_loss_terms(actuals, [naive_probs] * n)

    model_accuracy = sum(model_correct) / n
    favorite_accuracy = sum(favorite_correct) / n
    naive_accuracy = sum(naive_correct) / n
    model_log_loss = sum(model_ll_terms) / n
    naive_log_loss = sum(naive_ll_terms) / n

    ci = bootstrap_cis(
        {
            "model_acc": model_correct,
            "favorite_acc": favorite_correct,
            "naive_acc": naive_correct,
            "model_ll": model_ll_terms,
            "naive_ll": naive_ll_terms,
        }
    )

    def _pct_ci(key: str) -> str:
        lo, hi = ci[key]
        return f"[{lo:.1%}, {hi:.1%}]"

    def _ll_ci(key: str) -> str:
        lo, hi = ci[key]
        return f"[{lo:.3f}, {hi:.3f}]"

    print(f"\nBacktest — treino: 2018 ({n_train} jogos) · teste: 2022 ({n} jogos com ranking real)")
    print("1 único fold: sem ranking de 2018 não dá pra fazer k-fold.")
    print("Leia os números como indício, não validação robusta.")
    print("IC90% por bootstrap não-paramétrico (1000 reamostragens, seed=12345).\n")
    print(f"{'modelo (Poisson attack/def)':<32}")
    print(f"  accuracy: {model_accuracy:>6.1%}  IC90% {_pct_ci('model_acc')}")
    print(f"  log-loss: {model_log_loss:>6.3f}  IC90% {_ll_ci('model_ll')}")
    print(f"{'baseline: freq. ingênua 2018':<32}")
    print(f"  accuracy: {naive_accuracy:>6.1%}  IC90% {_pct_ci('naive_acc')}")
    print(f"  log-loss: {naive_log_loss:>6.3f}  IC90% {_ll_ci('naive_ll')}")
    print(f"{'baseline: favorito do ranking':<32}")
    print(f"  accuracy: {favorite_accuracy:>6.1%}  IC90% {_pct_ci('favorite_acc')}")
    print(f"  log-loss: {'n/a':>6}  (prediz sempre o rótulo, sem distribuição de probabilidade)")
