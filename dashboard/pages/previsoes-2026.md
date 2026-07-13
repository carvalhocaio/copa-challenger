---
title: Previsões 2026
description: O que o modelo projeta para a fase de grupos da próxima Copa
---

_O desk olha para trás em 2018 e 2022 — mas o pipeline preditivo também olha para frente. Estas são as **projeções do modelo** para os 72 jogos agendados da fase de grupos de 2026: gols esperados e probabilidade de vitória, empate e derrota por confronto._

<Note>
São **estimativas de um modelo** (Poisson sobre força ofensiva/defensiva treinada em 2018+2022, com fallback via ranking FIFA para seleções sem histórico), **não resultados**. Todos os jogos são tratados como neutros — a fonte não distingue sede real de neutra.
</Note>

## Quem o modelo mais favorece

```sql team_win_prob
select
    team,
    round(100.0 * avg(win_prob), 1) as prob_media_vitoria,
    count(*) as jogos
from (
    select home_team as team, prob_home_win as win_prob from copa.predictions_2026
    union all
    select away_team as team, prob_away_win as win_prob from copa.predictions_2026
)
group by team
order by prob_media_vitoria desc
limit 15
```

<BarChart
    data={team_win_prob}
    x=team
    y=prob_media_vitoria
    swapXY=true
    title="Probabilidade média de vitória por seleção — top 15"
    subtitle="Média da probabilidade de vitória projetada nos jogos de grupo de 2026"
    xAxisTitle="Seleção"
    yAxisTitle="% vitória média projetada"
    labels=true
/>

## Jogo a jogo

```sql matches
select
    date as data,
    home_team as mandante,
    away_team as visitante,
    expected_home_goals as xg_casa,
    expected_away_goals as xg_fora,
    prob_home_win as vitoria_casa,
    prob_draw as empate,
    prob_away_win as vitoria_fora
from copa.predictions_2026
order by data, mandante
```

<DataTable data={matches} rows=20 search=true>
    <Column id=data title="Data" fmt="d mmm"/>
    <Column id=mandante title="Mandante"/>
    <Column id=visitante title="Visitante"/>
    <Column id=xg_casa title="xG casa" fmt="0.0"/>
    <Column id=xg_fora title="xG fora" fmt="0.0"/>
    <Column id=vitoria_casa title="Vitória casa" fmt="pct1" contentType=colorscale scaleColor=green/>
    <Column id=empate title="Empate" fmt="pct1"/>
    <Column id=vitoria_fora title="Vitória fora" fmt="pct1" contentType=colorscale scaleColor=green/>
</DataTable>

_Leia como probabilidades, não certezas: numa fase de grupos, o próprio modelo espera que os favoritos tropecem em alguns jogos — é o que o [paradoxo do favorito](/favorito) mostra no histórico._
