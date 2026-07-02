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


def build_staging() -> None:
    """Cria/atualiza as views da camada `stg` e imprime um resumo."""
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS stg;")

    for rel_path in STAGING_MODELS:
        sql = (SQL_DIR / rel_path).read_text(encoding="utf-8")
        con.execute(sql)
        print(f"ok - {rel_path}")

    print("\n—— resumo da staging ——")
    for view in ("matches", "world_cup", "rankings"):
        n = scalar(con, f"SELECT count(*) FROM stg.{view}")
        print(f"  stg.{view}: {n:,} linhas")

    # sanity checks rápidos do escopo
    by_year = con.execute(
        "SELECT year, count(*) FROM stg.matches GROUP BY year ORDER BY year"
    ).fetchall()
    print("\n  partidas por edição:", dict(by_year))

    pens = scalar(con, "SELECT count(*) FROM stg.matches WHERE decided_on_pens")
    print(f"  decididas nos pênaltis: {pens}")

    xg_cov = scalar(con, "SELECT count(*) FROM stg.matches WHERE home_xg IS NOT NULL")
    print(f"  partidas com xG: {xg_cov}")

    con.close()
