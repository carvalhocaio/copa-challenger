"""Atributos de força ofensiva/defensiva por seleção, a partir dos marts.

Força = taxa de gols (blend 50/50 gol real / xG) por jogo, relativa à média
da competição, com shrinkage em direção a 1.0 proporcional ao nº de jogos —
sem isso, seleções com poucas partidas (early exits) geram forças extremas
por ruído de amostra, não sinal real.
"""

from __future__ import annotations

import duckdb
import polars as pl

from copa_challenger.config import DUCKDB_PATH

# peso do "prior" (seleção média) no shrinkage, em jogos equivalentes.
# heurística: não foi derivada de um empirical Bayes formal.
SHRINKAGE_K = 3.0


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


_STAT_COLS = ("matches", "goals_for", "goals_against", "xg_for", "xg_against")


def strength_from_stats(
    df: pl.DataFrame, league_avg: float, k: float = SHRINKAGE_K, blend_weight: float = 0.5
) -> pl.DataFrame:
    """Recebe team/matches/goals_for/goals_against/xg_for/xg_against, devolve
    team/matches/attack/defense. Maior = melhor nos dois eixos.

    `blend_weight` é o peso do gol real no blend gol/xG: blend = w*gol + (1-w)*xg.
    w=0.5 (default) reproduz a média 50/50 histórica.
    """
    w = blend_weight
    df = df.with_columns(pl.col(*_STAT_COLS).cast(pl.Float64))
    matches = pl.col("matches")
    blend_for = w * pl.col("goals_for") + (1 - w) * pl.col("xg_for")
    blend_against = w * pl.col("goals_against") + (1 - w) * pl.col("xg_against")
    raw_attack = (blend_for / matches) / league_avg
    raw_defense = (blend_against / matches) / league_avg

    return (
        df.with_columns(raw_attack.alias("raw_attack"), raw_defense.alias("raw_defense"))
        .with_columns(
            ((matches * pl.col("raw_attack") + k) / (matches + k)).alias("attack"),
            ((matches * pl.col("raw_defense") + k) / (matches + k)).alias("defense"),
        )
        .select("team", "matches", "attack", "defense")
    )


def _team_stats(con: duckdb.DuckDBPyConnection, years: list[int] | None) -> pl.DataFrame:
    """Estatísticas brutas por seleção. years=None usa o pooled 2018+2022
    (mart.team_strength_inputs); senão agrega mart.int_team_matches no recorte."""
    if years is None:
        return con.sql("""
            SELECT team, matches, goals_for, goals_against, xg_for, xg_against
            FROM mart.team_strength_inputs
        """).pl()
    years_sql = ", ".join(str(y) for y in years)
    return con.sql(f"""
        SELECT
            team,
            count(*) AS matches,
            sum(goals_for) AS goals_for,
            sum(goals_against) AS goals_against,
            sum(xg_for) AS xg_for,
            sum(xg_against) AS xg_against
        FROM mart.int_team_matches
        WHERE year IN ({years_sql})
        GROUP BY team
    """).pl()


def league_average_goals(
    con: duckdb.DuckDBPyConnection, years: list[int] | None = None, blend_weight: float = 0.5
) -> float:
    """Média de gols por seleção por jogo (blend gol/xG), no recorte de anos dado.
    `blend_weight` é o peso do gol real: blend = w*gol + (1-w)*xg (w=0.5 = 50/50)."""
    w = blend_weight
    stats = _team_stats(con, years)
    total_adj_goals = w * float(stats["goals_for"].sum()) + (1 - w) * float(stats["xg_for"].sum())
    return total_adj_goals / float(stats["matches"].sum())


def team_strength(
    con: duckdb.DuckDBPyConnection,
    years: list[int] | None = None,
    k: float = SHRINKAGE_K,
    blend_weight: float = 0.5,
) -> pl.DataFrame:
    """Força ofensiva/defensiva por seleção. years=None é o pooled 2018+2022
    (caminho de produção); years=[2018], por exemplo, é o caminho de backtest."""
    stats = _team_stats(con, years)
    avg = league_average_goals(con, years, blend_weight=blend_weight)
    return strength_from_stats(stats, avg, k=k, blend_weight=blend_weight)


def team_rankings_2026(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """Rank/pontos FIFA (ciclo 2026) das 48 seleções de raw.schedule_2026,
    resolvidos via seed.team_crosswalk."""
    return con.sql("""
        WITH teams AS (
            SELECT home_team AS team FROM raw.schedule_2026
            UNION
            SELECT away_team AS team FROM raw.schedule_2026
        )
        SELECT t.team, r.rank, r.points
        FROM teams t
        LEFT JOIN seed.team_crosswalk c ON c.match_name = t.team
        LEFT JOIN stg.rankings r
            ON r.team = COALESCE(c.ranking_name, t.team) AND r.cycle = 2026
    """).pl()


def team_rankings_2022(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """Rank/pontos FIFA (ciclo 2022) das seleções que jogaram a Copa de 2022,
    resolvidos via seed.team_crosswalk. Usado só no backtest."""
    return con.sql("""
        WITH teams AS (
            SELECT DISTINCT team FROM mart.int_team_matches WHERE year = 2022
        )
        SELECT t.team, r.rank, r.points
        FROM teams t
        LEFT JOIN seed.team_crosswalk c ON c.match_name = t.team
        LEFT JOIN stg.rankings r
            ON r.team = COALESCE(c.ranking_name, t.team) AND r.cycle = 2022
    """).pl()


def team_features(
    con: duckdb.DuckDBPyConnection,
    rankings: pl.DataFrame,
    years: list[int] | None = None,
    k: float = SHRINKAGE_K,
    blend_weight: float = 0.5,
) -> pl.DataFrame:
    """Junta rank/pontos (`rankings`) com força ofensiva/defensiva no recorte
    `years`. attack/defense vêm nulos para seleções sem histórico no recorte
    (`has_history=False`) — cabe ao model.py preencher via fallback."""
    strength = team_strength(con, years, k=k, blend_weight=blend_weight)
    return rankings.join(strength, on="team", how="left").with_columns(
        pl.col("matches").is_not_null().alias("has_history")
    )
