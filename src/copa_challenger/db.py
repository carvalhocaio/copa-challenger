"""Helpers compartilhados para consultas DuckDB."""

import duckdb


def scalar(con: duckdb.DuckDBPyConnection, sql: str) -> int:
    """Executa `sql` e retorna o primeiro valor da primeira linha."""
    row = con.execute(sql).fetchone()
    assert row is not None
    return row[0]
