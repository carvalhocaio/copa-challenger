"""Executa os modelos SQL (staging -> marts) sobre o DuckDB."""

import duckdb

from copa_challenger.config import DUCKDB_PATH, SQL_DIR
from copa_challenger.db import scalar

# ordem de execução importa: staging antes de marts.
STAGING_MODELS = [
    "staging/stg_matches.sql",
    "staging/stg_world_cup.sql",
    "staging/stg_rankings.sql",
]

MART_MODELS = [
    "marts/int_team_matches.sql",
    "marts/int_match_stages.sql",
    "marts/mart_team_performance.sql",
    "marts/mart_edition_kpis.sql",
    "marts/mart_knockout_analysis.sql",
    "marts/mart_ranking_vs_result.sql",
]


def _run_models(con: duckdb.DuckDBPyConnection, models: list[str]) -> None:
    for rel_path in models:
        sql = (SQL_DIR / rel_path).read_text(encoding="utf-8")
        con.execute(sql)
        print(f"ok - {rel_path}")


def build_all() -> None:
    """Cria/atualiza seeds, camadas stg e mart, e imprime um resumo."""
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS seed;")
    con.execute("CREATE SCHEMA IF NOT EXISTS stg;")
    con.execute("CREATE SCHEMA IF NOT EXISTS mart;")

    # seeds primeiro: marts dependem do crosswalk
    _run_models(con, ["seeds/team_crosswalk.sql"])
    _run_models(con, STAGING_MODELS)
    _run_models(con, MART_MODELS)

    print("\n── resumo ──")
    for view in (
        "stg.matches",
        "mart.int_team_matches",
        "mart.team_performance",
        "mart.edition_kpis",
        "mart.knockout_analysis",
        "mart.ranking_vs_result",
    ):
        n = scalar(con, f"SELECT count(*) FROM {view}")
        print(f"  {view}: {n:,} linhas")

    con.close()
