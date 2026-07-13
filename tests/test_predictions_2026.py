"""Testes da persistência das previsões de 2026 e do acesso via guardrail."""

import duckdb
import polars as pl
import pytest

from copa_challenger.agent import executor
from copa_challenger.predict import predict

_SAMPLE = pl.DataFrame({
    "round": ["Group stage", "Group stage"],
    "date": ["2026-06-11", "2026-06-12"],
    "home_team": ["Brazil", "Argentina"],
    "away_team": ["Serbia", "Mexico"],
    "expected_home_goals": [1.8, 1.5],
    "expected_away_goals": [0.9, 1.1],
    "prob_home_win": [0.62, 0.55],
    "prob_draw": [0.23, 0.26],
    "prob_away_win": [0.15, 0.19],
})


def _seed_db(path: str) -> None:
    con = duckdb.connect(path)
    con.execute("CREATE SCHEMA IF NOT EXISTS predict;")
    con.register("_s", _SAMPLE)
    con.execute("CREATE TABLE predict.predictions_2026 AS SELECT * FROM _s")
    con.close()


def test_persist_to_duckdb_round_trip(tmp_path, monkeypatch) -> None:
    db = tmp_path / "copa.duckdb"
    monkeypatch.setattr(predict, "DUCKDB_PATH", db)
    predict._persist_to_duckdb(_SAMPLE)

    con = duckdb.connect(str(db), read_only=True)
    n = con.execute("SELECT count(*) FROM predict.predictions_2026").fetchone()[0]
    con.close()
    assert n == 2


def test_persist_is_idempotent(tmp_path, monkeypatch) -> None:
    # CREATE OR REPLACE: rodar duas vezes não duplica linhas.
    db = tmp_path / "copa.duckdb"
    monkeypatch.setattr(predict, "DUCKDB_PATH", db)
    predict._persist_to_duckdb(_SAMPLE)
    predict._persist_to_duckdb(_SAMPLE)

    con = duckdb.connect(str(db), read_only=True)
    n = con.execute("SELECT count(*) FROM predict.predictions_2026").fetchone()[0]
    con.close()
    assert n == 2


@pytest.mark.parametrize(("a", "b"), [("Brazil", "Serbia"), ("Serbia", "Brazil")])
def test_prediction_query_matches_both_orientations(tmp_path, monkeypatch, a, b) -> None:
    # A tool casa o confronto independentemente de quem é mando no calendário.
    db = tmp_path / "copa.duckdb"
    _seed_db(str(db))
    monkeypatch.setattr(executor, "DUCKDB_PATH", db)

    result = executor.run_safe_sql(f"""
        SELECT home_team, away_team, prob_home_win
        FROM predict.predictions_2026
        WHERE (lower(home_team) = lower('{a}') AND lower(away_team) = lower('{b}'))
           OR (lower(home_team) = lower('{b}') AND lower(away_team) = lower('{a}'))
    """)
    assert result.row_count == 1
    assert result.rows[0][0] == "Brazil"
    assert result.rows[0][1] == "Serbia"
