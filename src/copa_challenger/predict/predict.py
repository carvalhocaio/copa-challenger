"""Gera as previsões da Copa de 2026 — Missão 04.

Uma linha por jogo de raw.schedule_2026 (72 jogos, todos de fase de grupos),
com gols esperados e probabilidades W/D/L. Força ofensiva/defensiva treinada
no pooled 2018+2022; seleções sem histórico (cold start) usam o fallback
via ranking FIFA. Jogos tratados como neutros (ver model.py).
"""

from __future__ import annotations

import duckdb
import polars as pl

from copa_challenger.config import DUCKDB_PATH, SUBMISSIONS_DIR
from copa_challenger.predict import features, model


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def _persist_to_duckdb(predictions: pl.DataFrame) -> None:
    """Materializa as previsões em predict.predictions_2026 (além do CSV), para o
    agente de chat consultá-las pelo mesmo guardrail dos dados históricos."""
    con = duckdb.connect(str(DUCKDB_PATH))  # read-write
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS predict;")
        con.register("_predictions_2026", predictions)
        con.execute(
            "CREATE OR REPLACE TABLE predict.predictions_2026 AS SELECT * FROM _predictions_2026"
        )
        con.unregister("_predictions_2026")
    finally:
        con.close()


def generate_predictions() -> pl.DataFrame:
    con = _con()

    rankings = features.team_rankings_2026(con)
    feats = features.team_features(con, rankings, years=None)
    fit = model.fit_fallback(feats)
    feats_full = model.apply_fallback(feats, fit)
    league_avg = features.league_average_goals(con, years=None)

    schedule = con.sql("""
        SELECT Round AS round, Date AS date, home_team, away_team
        FROM raw.schedule_2026
        ORDER BY Date
    """).pl()

    con.close()

    strength = {
        row["team"]: (row["attack"], row["defense"]) for row in feats_full.iter_rows(named=True)
    }

    rows = []
    for match in schedule.iter_rows(named=True):
        attack_home, defense_home = strength[match["home_team"]]
        attack_away, defense_away = strength[match["away_team"]]

        mu_home = model.expected_goals(attack_home, defense_away, league_avg)
        mu_away = model.expected_goals(attack_away, defense_home, league_avg)
        prob_home_win, prob_draw, prob_away_win = model.match_outcome_probs(mu_home, mu_away)

        rows.append({
            "round": match["round"],
            "date": match["date"],
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "expected_home_goals": round(mu_home, 3),
            "expected_away_goals": round(mu_away, 3),
            "prob_home_win": round(prob_home_win, 4),
            "prob_draw": round(prob_draw, 4),
            "prob_away_win": round(prob_away_win, 4),
        })

    predictions = pl.DataFrame(rows)

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SUBMISSIONS_DIR / "predictions_2026.csv"
    predictions.write_csv(out_path)
    _persist_to_duckdb(predictions)

    prob_sums = (
        predictions["prob_home_win"] + predictions["prob_draw"] + predictions["prob_away_win"]
    )
    print(f"ok - {predictions.height} jogos -> {out_path} + predict.predictions_2026")
    print(f"sanity: soma das probabilidades entre {prob_sums.min():.4f} e {prob_sums.max():.4f}")

    return predictions
