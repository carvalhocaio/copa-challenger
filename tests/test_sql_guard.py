"""Testes do guardrail de SQL - o anel de segurança do text-to-SQL."""

import pytest

from copa_challenger.agent.sql_guard import (
    SQLGuardError,
    enforce_row_limit,
    validate_sql,
)

# ── consultas legítimas: devem PASSAR ──
VALID = [
    "SELECT * FROM mart.edition_kpis",
    "SELECT team, attack_vs_xg FROM mart.team_performance WHERE year = 2022",
    "select round, count(*) from mart.int_match_stages group by round",
    """SELECT t.team FROM mart.team_performance t
       WHERE t.attack_vs_xg > (SELECT avg(attack_vs_xg) FROM mart.team_performance)""",
    "SELECT * FROM mart.edition_kpis UNION ALL SELECT * FROM mart.edition_kpis",
]

# ── ataques e violações: devem REPROVAR ──
MALICIOUS = [
    "DROP TABLE mart.edition_kpis",
    "DELETE FROM mart.team_performance",
    "UPDATE mart.team_performance SET goals_for = 99",
    "INSERT INTO mart.team_performance VALUES (1)",
    "SELECT * FROM mart.edition_kpis; DROP TABLE mart.edition_kpis",  # piggyback
    "SELECT * FROM raw.matches",  # fora da allowlist
    "SELECT * FROM stg.matches",  # camada não exposta
    "SELECT * FROM information_schema.tables",  # introspecção
    "ATTACH 'evil.db' AS evil",
    "COPY mart.edition_kpis TO 'out.csv'",
    "PRAGMA database_list",
    "CREATE TABLE hack AS SELECT * FROM mart.edition_kpis",
    "SELECT * FROM mart.team_performance JOIN raw.matches USING (year)",  # join proibido
]


@pytest.mark.parametrize("sql", VALID)
def test_valid_queries_pass(sql: str) -> None:
    assert validate_sql(sql)


@pytest.mark.parametrize("sql", MALICIOUS)
def test_malicious_queries_rejected(sql: str) -> None:
    with pytest.raises(SQLGuardError):
        validate_sql(sql)


def test_row_limit_appended_when_absent() -> None:
    out = enforce_row_limit("SELECT * FROM mart.edition_kpis", max_rows=50)
    assert "LIMIT 50" in out.upper()


def test_row_limit_reduces_oversized() -> None:
    out = enforce_row_limit("SELECT * FROM mart.edition_kpis LIMIT 10", max_rows=200)
    assert "10" in out
