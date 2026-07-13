"""Agente PydanticAI do World Cup Intelligence Desk.

Expõe 4 tools tipadas com SQL fixo para as perguntas mais comuns, mais
`run_sql` como escape hatch de text-to-SQL para o resto. O agente nunca
toca o banco direto: todo acesso passa por `executor.run_safe_sql`, que
valida e executa em conexão read-only (ver sql_guard.py).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from copa_challenger.agent.executor import run_safe_sql
from copa_challenger.agent.schema import render_schema_for_prompt
from copa_challenger.agent.sql_guard import SQLGuardError

load_dotenv()

_SYSTEM_PROMPT = f"""\
Você é o analista do World Cup Intelligence Desk — uma mesa de inteligência \
sobre as Copas do Mundo de 2018 e 2022. Responde perguntas de negócio com base \
EXCLUSIVAMENTE nos dados fornecidos pelas suas ferramentas.

Diretrizes:
- Use as ferramentas tipadas (get_team_performance, compare_editions, \
favorite_win_rate, list_shootouts) sempre que a pergunta se encaixar nelas.
- Para perguntas sobre um jogo específico da Copa de 2026, use get_prediction_2026 \
(ou run_sql sobre predict.predictions_2026). Deixe SEMPRE claro que são projeções do \
modelo, não resultados.
- Para perguntas fora do escopo dessas ferramentas, use run_sql com uma query \
SELECT sobre o schema `mart` (histórico) ou `predict` (previsões de 2026).
- NUNCA invente números. Se os dados não respondem, diga isso claramente.
- Responda em português, de forma concisa e analítica. Cite os números que embasam.
- Respeite as ressalvas de domínio abaixo à risca.

{render_schema_for_prompt()}
"""

_model = GoogleModel(
    "gemini-2.5-flash",
    provider=GoogleProvider(
        api_key=os.environ.get(
            "GEMINI_API_KEY",
            "",
        )
    ),
)

agent = Agent(_model, instructions=_SYSTEM_PROMPT)


# - typed tools -
@agent.tool_plain
def get_team_performance(team: str, year: int) -> str:
    """Performance de uma seleção numa edição (2018 ou 2022): gols, xG, eficiência."""
    r = run_safe_sql(f"""
        SELECT team, year, matches, goals_for, xg_for, attack_vs_xg,
               goals_against, xg_against, defense_vs_xg, goal_diff
        FROM mart.team_performance
        WHERE lower(team) = lower('{_esc(team)}') AND year = {int(year)}
    """)
    return r.to_markdown() if r.row_count else f"Sem dados para {team} em {year}."


@agent.tool_plain
def compare_editions() -> str:
    """Compara as edições de 2018 e 2022: KPIs de gols, xG, pênaltis, público, campeão."""
    return run_safe_sql("SELECT * FROM mart.edition_kpis ORDER BY year").to_markdown()


@agent.tool_plain
def favorite_win_rate() -> str:
    """Taxa de acerto do favorito (ranking FIFA) por fase — APENAS Copa de 2022."""
    return run_safe_sql("""
        SELECT
            CASE WHEN round = 'Group stage' THEN 'Fase de grupos' ELSE 'Mata-mata' END AS fase,
            count(*) FILTER (WHERE favorite_won IS NOT NULL) AS decididos,
            count(*) FILTER (WHERE favorite_won)            AS favorito_venceu,
            round(100.0 * count(*) FILTER (WHERE favorite_won)
                  / nullif(count(*) FILTER (WHERE favorite_won IS NOT NULL), 0), 1) AS pct
        FROM mart.ranking_vs_result
        GROUP BY fase ORDER BY fase
    """).to_markdown()


@agent.tool_plain
def list_shootouts() -> str:
    """Lista todas as disputas por pênaltis de 2018 e 2022, com fase e quem avançou."""
    return run_safe_sql("""
        SELECT year, round, home_team, away_team, winner
        FROM mart.int_match_stages
        WHERE decided_on_pens
        ORDER BY year, stage_order
    """).to_markdown()


@agent.tool_plain
def get_prediction_2026(team_a: str, team_b: str) -> str:
    """Previsão do modelo para um jogo da Copa de 2026 entre dois times.

    Projeção W/D/L e gols esperados (não é resultado). Casa o confronto em
    qualquer ordem mando/visitante do calendário.
    """
    a, b = _esc(team_a), _esc(team_b)
    r = run_safe_sql(f"""
        SELECT round, date, home_team, away_team,
               expected_home_goals, expected_away_goals,
               prob_home_win, prob_draw, prob_away_win
        FROM predict.predictions_2026
        WHERE (lower(home_team) = lower('{a}') AND lower(away_team) = lower('{b}'))
           OR (lower(home_team) = lower('{b}') AND lower(away_team) = lower('{a}'))
    """)
    if not r.row_count:
        return (
            f"Sem previsão de 2026 para {team_a} x {team_b} — só há jogos da fase "
            f"de grupos no calendário atual."
        )
    return r.to_markdown()


# - escape hatch text-to-SQL -
@agent.tool_plain
def run_sql(query: str) -> str:
    """Executa um SELECT sobre o schema `mart` para perguntas fora das tools fixas.

    A query é validada (só SELECT, só tabelas mart) e executada read-only.
    Use os nomes de tabela/coluna exatos do schema no system prompt.
    """
    try:
        r = run_safe_sql(query)
    except SQLGuardError as e:
        return f"Query rejeitada pelo guardrail de segurança: {e}"
    except Exception as e:  # erro de sintaxe/execução - devolve ao LLM para corrigir
        return f"Erro ao executar: {e}"
    return r.to_markdown() if r.row_count else "_(a query não retornou linhas)_"


def _esc(value: str) -> str:
    """Escapa aspas simples para interpolação segura em literais SQL das typed tools."""
    return value.replace("'", "''")
