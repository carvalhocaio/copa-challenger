"""Missão 02 — EDA: World Cup Intelligence Desk.

EDA reativa (marimo). Não reexplora o dataset do zero: parte dos marts da
Missão 01 e transforma número em evidência visual, testando as nuances que
as tabelas esconderam. Cada gráfico fecha com um "so what".

Rodar:   uv run marimo edit notebooks/02_eda.py
Exportar: uv run marimo export html notebooks/02_eda.py -o notebooks/02_eda.html
"""

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import polars as pl

    from copa_challenger.analytics import queries

    return alt, mo, pl, queries


@app.cell
def _(mo):
    mo.md("""
    # World Cup Intelligence Desk — EDA
    **Missão 02** · Rússia 2018 × Catar 2022

    Cada seção testa uma hipótese que a Missão 01 levantou mas não
    conseguiu mostrar visualmente. Fonte: camada `mart` (DuckDB).
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 1 · A média engana? Distribuição de gols por partida
    """)
    return


@app.cell
def _(alt, queries):
    df_m = queries.matches()

    goals_hist = (
        alt.Chart(df_m)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X("total_goals:O", title="Gols na partida"),
            y=alt.Y("count():Q", title="Nº de partidas"),
            color=alt.Color("year:N", title="Edição"),
            xOffset="year:N",
        )
        .properties(height=280, title="Distribuição de gols por partida")
    )
    goals_hist
    return (df_m,)


@app.cell
def _(mo):
    mo.md("""
    **So what:** as médias quase idênticas (2.64 vs 2.69) escondem a
    *forma* da distribuição — se um torneio concentrou mais goleadas ou
    mais jogos truncados, a mediana e a cauda contam história diferente
    da média.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2 · Calibração do xG — quem mereceu o placar?
    """)
    return


@app.cell
def _(alt, df_m):
    # scatter: gols reais (total) vs xG total, com linha de calibração y=x
    base = alt.Chart(df_m)

    pts = base.mark_circle(size=70, opacity=0.6).encode(
        x=alt.X("xg_total:Q", title="xG total da partida"),
        y=alt.Y("total_goals:Q", title="Gols reais da partida"),
        color=alt.Color("year:N", title="Edição"),
        tooltip=["year", "round", "home_team", "away_team", "total_goals", "xg_total"],
    )

    line = base.mark_line(strokeDash=[4, 4], color="gray").encode(
        x="xg_total:Q",
        y="xg_total:Q",
    )

    (pts + line).properties(height=340, title="Placar real vs esperado (xG)")
    return


@app.cell
def _(mo):
    mo.md("""
    **So what:** pontos acima da linha = partidas que renderam mais gols
    que o esperado (eficiência ou sorte na finalização); abaixo = jogos
    "travados" que mereciam mais. É a base do eixo analítico do desk.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3 · A curva do favorito: o ranking prevê melhor no mata-mata?
    """)
    return


@app.cell
def _(alt, pl, queries):
    df_fav = queries.favorite_by_round().with_columns(
        ("n=" + pl.col("decided").cast(pl.Utf8)).alias("n_label")
    )

    bars = (
        alt.Chart(df_fav)
        .mark_bar()
        .encode(
            x=alt.X("round:N", sort=alt.SortField("stage_order"), title="Rodada"),
            y=alt.Y("favorite_win_pct:Q", title="% vitória do favorito"),
            # opacidade proporcional à amostra: barras "fracas" = poucos jogos
            opacity=alt.Opacity(
                "decided:Q",
                scale=alt.Scale(range=[0.35, 1.0]),
                title="Jogos decididos (n)",
            ),
            tooltip=["round", "decided", "favorite_won", "favorite_win_pct"],
        )
    )

    labels = (
        alt.Chart(df_fav)
        .mark_text(dy=-6, color="gray", fontSize=11)
        .encode(
            x=alt.X("round:N", sort=alt.SortField("stage_order")),
            y=alt.Y("favorite_win_pct:Q"),
            text="n_label:N",
        )
    )

    (bars + labels).properties(
        height=300,
        title="Acerto do favorito (ranking 2022) por fase — barra mais clara = amostra menor",
    )
    return (df_fav,)


@app.cell
def _(df_fav, mo):
    mo.md(f"""
    **So what:** por *partida*, o favorito acerta mais no mata-mata que
    nos grupos — mas cada rodada tem poucos jogos ({df_fav["decided"].sum()}
    decididos no total). O paradoxo do "nº 1 nunca campeão" não está na
    partida isolada, e sim na **sequência**: vencer ~7 jogos seguidos a
    81% cada dá ~23% de levar a taça. Amostra de uma edição — indício,
    não prova.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 4 · O mapa dos campeões: ataque × defesa (ambos vs xG)
    """)
    return


@app.cell
def _(alt, pl, queries):
    df_tp = queries.team_performance().filter(pl.col("matches") >= 4)

    quad = (
        alt.Chart(df_tp)
        .mark_circle(size=90, opacity=0.7)
        .encode(
            x=alt.X("attack_vs_xg:Q", title="Ataque vs xG  (→ finaliza acima do esperado)"),
            y=alt.Y("defense_vs_xg:Q", title="Defesa vs xG  (↑ sofre menos que o esperado)"),
            color=alt.Color("year:N", title="Edição"),
            tooltip=["team", "year", "attack_vs_xg", "defense_vs_xg", "goal_diff"],
        )
        .properties(
            height=380,
            title="Quadrante de eficiência — candidatos a título no canto superior direito",
        )
    )

    rule_x = alt.Chart(df_tp).mark_rule(color="gray", opacity=0.4).encode(x=alt.datum(0))
    rule_y = alt.Chart(df_tp).mark_rule(color="gray", opacity=0.4).encode(y=alt.datum(0))

    (quad + rule_x + rule_y)
    return


@app.cell
def _(mo):
    mo.md("""
    **So what:** o quadrante superior-direito reúne quem foi eficiente dos
    dois lados. As linhas de referência em zero separam eficiência real de
    dependência de xG — e é aí que os finalistas tendem a aparecer.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 5 · O fator pênalti — quem se salvou nos 11 metros
    """)
    return


@app.cell
def _(mo, queries):
    df_pens = queries.shootouts()
    mo.ui.table(df_pens, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    **So what:** as disputas por pênaltis concentram-se no mata-mata e
    decidem confrontos onde o jogo terminou empatado — sorte estruturada.
    Croácia (2018) construiu boa parte da campanha de vice justamente aqui.
    """)
    return


if __name__ == "__main__":
    app.run()
