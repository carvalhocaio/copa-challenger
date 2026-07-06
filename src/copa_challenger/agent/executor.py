"""Execução segura de SQL contra a camada mart — o anel final de defesa.

Fluxo: valida (sql_guard) → força LIMIT → conexão READ-ONLY → executa.
Isolado do agente de propósito: testável sem LLM, e concentra todo o acesso
ao banco num único ponto auditável.
"""

from __future__ import annotations

import duckdb

from copa_challenger.agent.sql_guard import (
    MAX_ROWS_DEFAULT,
    enforce_row_limit,
    validate_sql,
)
from copa_challenger.config import DUCKDB_PATH


class QueryResult:
    """Resultado tipado de uma consulta: colunas + linhas + o SQL efetivamente rodado."""

    def __init__(self, columns: list[str], rows: list[tuple], executed_sql: str) -> None:
        self.columns = columns
        self.rows = rows
        self.executed_sql = executed_sql

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def to_markdown(self, max_display: int = 30) -> str:
        """Renderiza como tabela markdown (para a resposta do agente / Streamlit)."""
        if not self.rows:
            return "_(sem resultados)_"
        head = "| " + " | ".join(self.columns) + " |"
        sep = "| " + " | ".join("---" for _ in self.columns) + " |"
        body = ["| " + " | ".join(_fmt(v) for v in row) + " |" for row in self.rows[:max_display]]
        table = "\n".join([head, sep, *body])
        if self.row_count > max_display:
            table += f"\n\n_… {self.row_count - max_display} linhas adicionais omitidas._"
        return table


def _fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def run_safe_sql(sql: str, max_rows: int = MAX_ROWS_DEFAULT) -> QueryResult:
    """Valida, limita e executa um SELECT read-only. Levanta SQLGuardError se reprovar."""
    validated = validate_sql(sql)  # anel 1: AST (só SELECT, só allowlist)
    limited = enforce_row_limit(validated, max_rows)  # anel 2: cap de linhas

    # anel 3: conexão fisicamente read-only — mutação é impossível na raiz
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        cur = con.execute(limited)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
    finally:
        con.close()

    return QueryResult(columns=columns, rows=rows, executed_sql=limited)
