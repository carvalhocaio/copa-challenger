"""Guardrail de SQL para o escape hatch text-to-SQL do agente.

Valida, via AST (sqlglot), que o SQL gerado pelo LLM é seguro ANTES de tocar
o banco. Defesa em profundidade — este é o primeiro anel; a conexão read-only
e o cap de linhas são os anéis seguintes.

Regras (todas obrigatórias):
  1. Statement único (sem múltiplos comandos encadeados por ';').
  2. Exclusivamente SELECT (nenhum DDL/DML/PRAGMA/ATTACH/COPY/CALL).
  3. Toda tabela referenciada está na ALLOWLIST (schema `mart`).
  4. Sem CTE recursiva nem subquery apontando fora da allowlist.
"""

from __future__ import annotations

import typing as t

import sqlglot
from sqlglot import exp

from copa_challenger.agent.schema import ALLOWED_TABLES

# Comandos que, se aparecerem como nó raiz ou aninhado, reprovam na hora.
# Expression é reexportado por sqlglot via wildcard import sem __all__; o type
# checker não reconhece isso como export público, daí o ignore abaixo.
_FORBIDDEN_NODES: tuple[type[exp.Expression], ...] = (  # type: ignore[attr-defined]
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,  # Command cobre PRAGMA/ATTACH/COPY/SET/CALL etc.
)

_DIALECT = "duckdb"
MAX_ROWS_DEFAULT = 200


class SQLGuardError(ValueError):
    """SQL reprovado pelo guardrail. A mensagem é segura para exibir ao usuário."""


def validate_sql(sql: str) -> str:
    """Valida o SQL e devolve a versão normalizada. Levanta SQLGuardError se reprovar."""
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise SQLGuardError("SQL vazio.")

    # 1. statement único — parse_all pega múltiplos comandos
    statements = sqlglot.parse(sql, dialect=_DIALECT)
    if len(statements) != 1:
        raise SQLGuardError("Apenas um comando SELECT é permitido por vez.")

    tree = statements[0]
    if tree is None:
        raise SQLGuardError("Não foi possível interpretar o SQL.")

    # 2. raiz precisa ser SELECT (ou um SELECT entre parênteses)
    root = tree.unnest() if isinstance(tree, exp.Subquery) else tree
    if not isinstance(root, (exp.Select, exp.Union)):
        raise SQLGuardError("Somente consultas SELECT são permitidas.")

    # 3. nenhum nó proibido em qualquer profundidade da árvore
    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise SQLGuardError("Operação não permitida: apenas leitura (SELECT) é autorizada.")

    # 4. toda tabela referenciada precisa estar na allowlist
    for table in tree.find_all(exp.Table):
        qualified = _qualified_name(table)
        if qualified not in ALLOWED_TABLES:
            raise SQLGuardError(
                f"Tabela não autorizada: '{qualified}'. "
                f"Somente as tabelas do schema `mart` são consultáveis."
            )

    return sql


def _qualified_name(table: exp.Table) -> str:
    """Reconstrói 'schema.tabela' a partir do nó, ignorando aliases."""
    parts = [p.name for p in (table.args.get("db"), table.this) if p is not None]
    return ".".join(parts)


def enforce_row_limit(sql: str, max_rows: int = MAX_ROWS_DEFAULT) -> str:
    """Garante um LIMIT no SELECT. Se já houver um maior, reduz para max_rows."""
    tree = sqlglot.parse_one(sql, dialect=_DIALECT)
    existing = tree.args.get("limit")
    if existing is not None:
        try:
            current = int(existing.expression.name)
            if current <= max_rows:
                return sql
        except (AttributeError, ValueError):
            pass
    # validate_sql já garantiu que a raiz é Select/Union, então sempre é um Query
    # (parse_one só devolve o tipo genérico Expr por causa da assinatura).
    query = t.cast(exp.Query, tree)
    return query.limit(max_rows).sql(dialect=_DIALECT)
