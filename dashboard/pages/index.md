---
title: World Cup Intelligence Desk
description: Rússia 2018 × Catar 2022 — leitura analítica de duas Copas
---

_Mesa de inteligência da Copa do Mundo. Duas edições, 128 partidas, uma pergunta: o que os dados de 2018 e 2022 nos contam sobre como se vence — e como não se vence — um Mundial._

## O panorama

```sql kpis
select
    sum(n_matches)                       as partidas,
    sum(total_goals)                     as gols,
    round(avg(goals_per_match), 2)       as media_gols,
    sum(pen_shootouts)                   as disputas_penaltis
from copa.edition_kpis
```

<BigValue data={kpis} value=partidas title="Partidas analisadas"/>
<BigValue data={kpis} value=gols title="Gols marcados"/>
<BigValue data={kpis} value=media_gols title="Gols por partida"/>
<BigValue data={kpis} value=disputas_penaltis title="Disputas por pênaltis"/>

## Duas Copas, dois temperamentos

As médias quase idênticas — **2,64** gols por jogo em 2018, **2,69** em 2022 — escondem torneios de personalidade oposta. A distribuição por partida revela o que a média apaga: Catar 2022 foi mais **polarizado**, com mais jogos secos _e_ mais goleadas nas pontas, enquanto Rússia 2018 concentrou-se na faixa de 1 a 3 gols.

```sql goals_dist
select
    total_goals,
    year,
    count(*) as partidas
from copa.matches
group by total_goals, year
order by total_goals
```

<BarChart
    data={goals_dist}
    title="Distribuição de gols por partida"
    subtitle="Nº de partidas por total de gols, comparando as edições"
    x=total_goals
    y=partidas
    series=year
    type=grouped
    xAxisTitle="Gols na partida"
    yAxisTitle="Partidas"
/>

## Onde a análise vai

Este desk se desdobra em duas leituras. **[As duas Copas](/edicoes)** compara Rússia e Catar em eficiência ofensiva e defensiva — quem mereceu o placar e quem viveu de finalização. **[O paradoxo do favorito](/favorito)** enfrenta a pergunta que o ranking FIFA não responde: por que o número 1 nunca levantou a taça.
