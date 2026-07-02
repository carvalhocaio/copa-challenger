"""Ingestão dos CSVs brutos para o DuckDB (camada raw)."""

import duckdb

from copa_challenger.config import DUCKDB_PATH, RAW_DATA_DIR
from copa_challenger.db import scalar

# mapeamento explícito arquivo -> tabela na camada raw.
# nomes de ranking carregam a data no arquivo; encurtamos para o ciclo.
TABLE_MAP = {
    "matches_1930_2022.csv": "matches",
    "world_cup.csv": "world_cup",
    "schedule_2026.csv": "schedule_2026",
    "fifa_ranking_2022-10-06.csv": "ranking_2022",
    "fifa_ranking_2026-06-08.csv": "ranking_2026",
}


def ingest_raw() -> None:
    """Carrega cada CSV de data/raw/ em uma tabela no schema `raw` do DuckDB.

    Usa read_csv_auto com sample_size=-1 (varre o arquivo inteiro para
    inferir tipos, evitando erros de inferência em colunas esparsas).
    Ao final, imprime o schema e a contagem de cada tabela.
    """
    missing = [f for f in TABLE_MAP if not (RAW_DATA_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Arquivos ausentes em {RAW_DATA_DIR}: {missing}. Rode `uv run copa download` primeiro."
        )

    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    for filename, table in TABLE_MAP.items():
        csv_path = RAW_DATA_DIR / filename
        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw.{table} AS
            SELECT * FROM read_csv_auto(?, sample_size=-1, header=true);
            """,
            [str(csv_path)],
        )
        print(f"raw.{table}  <-  {filename}")

    print(f"\nIngestão concluída em {DUCKDB_PATH}\n")
    _print_catalog(con)
    con.close()


def _print_catalog(con: duckdb.DuckDBPyConnection) -> None:
    """Imprime schema (coluna: tipo) e nº de linhas de cada tabela raw."""
    for table in TABLE_MAP.values():
        n = scalar(con, f"SELECT count(*) FROM raw.{table}")
        cols = con.execute(f"DESCRIBE raw.{table}").fetchall()
        print(f"── raw.{table}  ({n:,} linhas)")
        for col in cols:
            name, dtype = col[0], col[1]
            print(f"     {name}: {dtype}")
        print()
