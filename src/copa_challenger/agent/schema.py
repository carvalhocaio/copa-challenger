"""Contexto semântico da camada `mart` - o que o agente enxerga do modelo.

Esta é a fundação do text-to-SQL seguro: o agente só conhece as tabelas e
colunas descritas aqui. `ALLOWED_TABLES` alimenta o guardrail de allowlist;
`render_schema_for_prompt()` e `DATA_CAVEATS` alimentam o system prompt.

Toda a semântica não-óbvia (convenção de sinal do xG, ausência de ranking em
2018, empates NULL) vive aqui - é o conhecimento de domínio virando guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    description: str


@dataclass(frozen=True)
class Table:
    name: str
    grain: str
    columns: tuple[Column, ...]


MART_TABLES: tuple[Table, ...] = (
    Table(
        name="mart.edition_kpis",
        grain="uma linha por edição (2018, 2022)",
        columns=(
            Column("year", "BIGINT", "ano da edição (2018 ou 2022)"),
            Column("host", "VARCHAR", "país-sede"),
            Column("n_matches", "BIGINT", "total de partidas (64 por edição)"),
            Column("total_goals", "BIGINT", "gols na edição"),
            Column("goals_per_match", "DOUBLE", "média de gols por partida"),
            Column("xg_per_match", "DOUBLE", "média de xG por partida"),
            Column("goals_minus_xg", "DOUBLE", "gols/jogo − xG/jogo (eficiência do torneio)"),
            Column("pen_shootouts", "BIGINT", "nº de disputas por pênaltis"),
            Column("avg_attendance", "DOUBLE", "público médio"),
            Column("champion", "VARCHAR", "campeão"),
            Column("runner_up", "VARCHAR", "vice-campeão"),
            Column("top_scorer", "VARCHAR", "artilheiro (nome - gols)"),
        ),
    ),
    Table(
        name="mart.team_performance",
        grain="uma linha por (seleção, edição)",
        columns=(
            Column("team", "VARCHAR", "seleção"),
            Column("year", "BIGINT", "edição"),
            Column("matches", "BIGINT", "jogos disputados na edição"),
            Column("wins_reg", "BIGINT", "vitórias no tempo normal"),
            Column("draws", "BIGINT", "empates"),
            Column("losses_reg", "BIGINT", "derrotas no tempo normal"),
            Column("advanced_or_won", "BIGINT", "jogos em que avançou/venceu (inclui pênaltis)"),
            Column("goals_for", "BIGINT", "gols marcados"),
            Column("goals_against", "BIGINT", "gols sofridos"),
            Column("goal_diff", "BIGINT", "saldo de gols"),
            Column("xg_for", "DOUBLE", "xG a favor (chances criadas, em gols esperados)"),
            Column("xg_against", "DOUBLE", "xG concedido ao adversário"),
            Column(
                "attack_vs_xg",
                "DOUBLE",
                "gols_for − xg_for. POSITIVO = finalizou ACIMA do esperado "
                "(eficiência/sorte na finalização). NÃO significa 'atacou mais'.",
            ),
            Column(
                "defense_vs_xg",
                "DOUBLE",
                "xg_against − goals_against. POSITIVO = defesa MELHOR que o "
                "esperado (sofreu menos que o xG concedido). Fórmula invertida "
                "em relação ao ataque, de propósito: nos dois eixos, maior = melhor.",
            ),
        ),
    ),
    Table(
        name="mart.int_match_stages",
        grain="uma linha por partida, com metadados de fase",
        columns=(
            Column("year", "BIGINT", "edição"),
            Column(
                "round",
                "VARCHAR",
                "fase: 'Group stage', 'Round of 16', 'Quarter-finals', "
                "'Semi-finals', 'Third-place match', 'Final'",
            ),
            Column("stage_type", "VARCHAR", "'group' ou 'knockout'"),
            Column("stage_order", "INTEGER", "ordem cronológica da fase (1=grupos … 6=final)"),
            Column("home_team", "VARCHAR", "mandante"),
            Column("away_team", "VARCHAR", "visitante"),
            Column("home_score", "BIGINT", "gols do mandante (tempo normal + prorrogação)"),
            Column("away_score", "BIGINT", "gols do visitante"),
            Column("home_xg", "DOUBLE", "xG do mandante"),
            Column("away_xg", "DOUBLE", "xG do visitante"),
            Column("total_goals", "BIGINT", "gols na partida"),
            Column("decided_on_pens", "BOOLEAN", "decidida em disputa por pênaltis?"),
            Column(
                "winner",
                "VARCHAR",
                "vencedor (inclui decisão por pênaltis). NULL em empate real da fase de grupos.",
            ),
            Column("attendance", "BIGINT", "público"),
            Column("venue", "VARCHAR", "estádio"),
        ),
    ),
    Table(
        name="mart.int_team_matches",
        grain="uma linha por (partida, seleção) — visão 'do time'",
        columns=(
            Column("year", "BIGINT", "edição"),
            Column("round", "VARCHAR", "fase"),
            Column("team", "VARCHAR", "seleção"),
            Column("opponent", "VARCHAR", "adversário"),
            Column("is_home", "BOOLEAN", "jogou como mandante?"),
            Column("goals_for", "BIGINT", "gols marcados na partida"),
            Column("goals_against", "BIGINT", "gols sofridos na partida"),
            Column("xg_for", "DOUBLE", "xG a favor na partida"),
            Column("xg_against", "DOUBLE", "xG concedido na partida"),
            Column("decided_on_pens", "BOOLEAN", "partida decidida nos pênaltis?"),
            Column("result", "VARCHAR", "'win' / 'draw' / 'loss' (tempo normal)"),
            Column("won_match", "BOOLEAN", "venceu, incluindo decisão por pênaltis"),
        ),
    ),
    Table(
        name="mart.knockout_analysis",
        grain="uma linha por (edição, fase de mata-mata)",
        columns=(
            Column("year", "BIGINT", "edição"),
            Column("round", "VARCHAR", "fase de mata-mata"),
            Column("stage_order", "INTEGER", "ordem da fase"),
            Column("n_matches", "BIGINT", "partidas na fase"),
            Column("goals_per_match", "DOUBLE", "média de gols na fase"),
            Column("xg_per_match", "DOUBLE", "média de xG na fase"),
            Column("pen_shootouts", "BIGINT", "disputas por pênaltis na fase"),
        ),
    ),
    Table(
        name="mart.ranking_vs_result",
        grain="uma linha por partida de 2022 (APENAS 2022)",
        columns=(
            Column("round", "VARCHAR", "fase"),
            Column("home_team", "VARCHAR", "mandante"),
            Column("away_team", "VARCHAR", "visitante"),
            Column("home_rank", "BIGINT", "rank FIFA do mandante (out/2022)"),
            Column("away_rank", "BIGINT", "rank FIFA do visitante"),
            Column("winner", "VARCHAR", "vencedor; NULL em empate real de grupos"),
            Column("higher_ranked", "VARCHAR", "seleção mais bem ranqueada do confronto"),
            Column(
                "favorite_won",
                "BOOLEAN",
                "o favorito (menor rank) venceu? NULL em empate real de grupos",
            ),
        ),
    ),
)

# Tabela de previsões de 2026 (schema `predict`) — projeções do modelo, não histórico.
PREDICT_TABLES: tuple[Table, ...] = (
    Table(
        name="predict.predictions_2026",
        grain="uma linha por jogo agendado da Copa de 2026 (72 jogos, fase de grupos)",
        columns=(
            Column("round", "VARCHAR", "fase (todos 'Group stage' no calendário atual)"),
            Column("date", "DATE", "data do jogo"),
            Column("home_team", "VARCHAR", "seleção mandante no calendário"),
            Column("away_team", "VARCHAR", "seleção visitante no calendário"),
            Column("expected_home_goals", "DOUBLE", "gols esperados do mandante (modelo Poisson)"),
            Column("expected_away_goals", "DOUBLE", "gols esperados do visitante"),
            Column("prob_home_win", "DOUBLE", "probabilidade projetada de vitória do mandante"),
            Column("prob_draw", "DOUBLE", "probabilidade projetada de empate"),
            Column("prob_away_win", "DOUBLE", "probabilidade projetada de vitória do visitante"),
        ),
    ),
)

# Allowlist do guardrail: só estas tabelas podem ser referenciadas pelo SQL.
ALLOWED_TABLES: frozenset[str] = frozenset(t.name for t in (*MART_TABLES, *PREDICT_TABLES))

# Avisos de domínio injetados no system prompt - blindam contra alucinação.
DATA_CAVEATS: tuple[str, ...] = (
    "Escopo: APENAS Copas de 2018 e 2022 (128 partidas). Não invente outras edições.",
    "Ranking FIFA só existe para 2022 (mart.ranking_vs_result). NÃO há ranking de "
    "2018 — nunca afirme favoritismo por ranking em 2018.",
    "attack_vs_xg positivo = finalizou acima do esperado, NÃO 'atacou mais'. "
    "Sempre leia junto com xg_for para dar contexto de volume.",
    "defense_vs_xg positivo = defendeu melhor que o esperado (fórmula xg_against − "
    "goals_against, invertida em relação ao ataque).",
    "winner e favorite_won são NULL em empates reais da fase de grupos.",
    "Amostras são pequenas (uma ou duas edições). Reporte tendências como indício, "
    "não prova estatística.",
    "predict.predictions_2026 são PROJEÇÕES do modelo para a Copa de 2026 (72 jogos da "
    "fase de grupos), NÃO resultados. Deixe SEMPRE explícito que são estimativas.",
    "As previsões de 2026 tratam todos os jogos como neutros (sem vantagem de mando): a "
    "fonte não distingue sede real de sede neutra.",
)


def render_schema_for_prompt() -> str:
    """Renderiza o schema `mart` como bloco de texto compacto para o system prompt."""
    lines: list[str] = ["TABELAS DISPONÍVEIS (schema `mart`, somente leitura):", ""]
    for t in MART_TABLES:
        lines.append(f"### {t.name} - {t.grain}")
        for c in t.columns:
            lines.append(f" - {c.name} ({c.type}): {c.description}")
        lines.append("")
    lines.append("PREVISÕES DE 2026 (schema `predict`, somente leitura):")
    lines.append("Projeções do modelo para a próxima Copa — NÃO são dados históricos.")
    lines.append("")
    for t in PREDICT_TABLES:
        lines.append(f"### {t.name} - {t.grain}")
        for c in t.columns:
            lines.append(f" - {c.name} ({c.type}): {c.description}")
        lines.append("")
    lines.append("REGRAS E RESSALVAS DE DOMÍNIO:")
    for caveat in DATA_CAVEATS:
        lines.append(f" - {caveat}")
    return "\n".join(lines)
