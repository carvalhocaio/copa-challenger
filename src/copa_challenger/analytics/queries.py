"""Consultas da EDA (Missão 02) — retornam DataFrames Polars a partir dos marts.

Centraliza o SQL para manter o notebook limpo e as queries testáveis/
reaproveitáveis no dashboard (Missão 03).
"""

from __future__ import annotations

import duckdb
import polars as pl

from copa_challenger.config import DUCKDB_PATH


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def matches() -> pl.DataFrame:
    """Grão de partida: uma linha por jogo, com xG, fase e desfacho."""
    with _con() as con:
        return con.sql("""
            SELECT
                year, round, stage_type, stage_order,
                home_team, away_team, home_score, away_score,
                home_xg, away_xg, total_goals,
                (home_xg + away_xg) AS xg_total,
                decided_on_pens, winner
            FROM mart.int_match_stages
            ORDER BY year, stage_order, match_date
        """).pl()


def team_performance() -> pl.DataFrame:
    """Grão de (seleção, edição): KPIs ofensivos/defensivos e deltas de xG."""
    with _con() as con:
        return con.sql("""
            SELECT team, year, matches,
                   goals_for, goals_against, goal_diff,
                   xg_for, xg_against,
                   attack_vs_xg, defense_vs_xg
            FROM mart.team_performance
        """).pl()


def favorite_by_round() -> pl.DataFrame:
    """Taxa de acerto do favorito (ranking 2022) por rodada, na ordem do torneio."""
    with _con() as con:
        return con.sql("""
            SELECT
                round,
                any_value(CASE
                    WHEN round = 'Group stage'       THEN 1
                    WHEN round = 'Round of 16'       THEN 2
                    WHEN round = 'Quarter-finals'    THEN 3
                    WHEN round = 'Semi-finals'       THEN 4
                    WHEN round = 'Third-place match' THEN 5
                    WHEN round = 'Final'             THEN 6
                END) AS stage_order,
                count(*) FILTER (WHERE favorite_won IS NOT NULL) AS decided,
                count(*) FILTER (WHERE favorite_won)             AS favorite_won,
                round(100.0 * count(*) FILTER (WHERE favorite_won)
                        / nullif(count(*) FILTER (WHERE favorite_won IS NOT NULL), 0), 1)
                                                                    AS favorite_win_pct
            FROM mart.ranking_vs_result
            GROUP BY round
            HAVING count(*) FILTER (WHERE favorite_won IS NOT NULL) > 0
            ORDER BY stage_order
        """).pl()


def shootouts() -> pl.DataFrame:
    """As disputas por pênaltis do escopo: fase, confronto e quem avançou."""
    with _con() as con:
        return con.sql("""
            SELECT year, round, stage_order,
                   home_team, away_team, home_score, away_score, winner
            FROM mart.int_match_stages
            WHERE decided_on_pens
            ORDER BY year, stage_order
        """).pl()
