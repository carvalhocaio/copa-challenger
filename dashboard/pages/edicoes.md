---
title: As duas Copas
description: Rússia 2018 × Catar 2022 — quem mereceu o placar
---

_Se o gol é o que aconteceu, o **xG** é o que deveria ter acontecido. Comparar os dois separa mérito de sorte — e é aqui que Rússia e Catar mostram do que foram feitas._

## Placar real vs. esperado

Cada ponto é uma partida. A linha tracejada é a calibração perfeita: em cima dela, o placar bateu com o xG. **Acima**, saíram mais gols do que as chances mereciam — eficiência clínica ou noite abençoada. **Abaixo**, o jogo travou e o placar ficou aquém do volume de chances.

```sql calibration
select
    year,
    round,
    home_team || ' × ' || away_team as confronto,
    total_goals,
    xg_total,
    round(total_goals - xg_total, 2) as delta
from copa.matches
order by xg_total
```

<ScatterPlot
    data={calibration}
    x=xg_total
    y=total_goals
    series=year
    xAxisTitle="xG total da partida"
    yAxisTitle="Gols reais da partida"
    tooltipTitle=confronto
/>

O canto superior direito guarda os festivais — a final Argentina 3×3 França (xG 5,5) foi tão caótica quanto os números prometiam. Já a faixa inferior reúne os duelos de xadrez, decididos no detalhe apesar do volume de chances.

## O mapa dos campeões

Aqui cada ponto é uma **seleção numa edição**, posicionada por eficiência dos dois lados: à direita, ataca acima do esperado; acima, defende melhor que o xG concedido. O quadrante superior-direito é a zona dos completos — quem foi eficiente atacando _e_ defendendo. Não por acaso, é onde os finalistas moram.

```sql efficiency
select
    team,
    year,
    matches,
    attack_vs_xg,
    defense_vs_xg,
    goal_diff
from copa.team_performance
where matches >= 4
order by (attack_vs_xg + defense_vs_xg) desc
```

<ScatterPlot
    data={efficiency}
    x=attack_vs_xg
    y=defense_vs_xg
    series=year
    xAxisTitle="Ataque vs xG  →  finaliza acima do esperado"
    yAxisTitle="Defesa vs xG  →  sofre menos que o esperado"
    tooltipTitle=team
    xMin=-4
    yMin=-4
/>

<Note>
Filtro de 4+ jogos: exclui quem caiu na fase de grupos, onde 3 partidas dão amostra curta demais para separar eficiência de ruído.
</Note>

A leitura fina: a **Croácia 2022** aparece no alto do eixo defensivo — segurou adversários muito abaixo do xG concedido e transformou isso em campanha de semifinal. A **França**, nas duas edições, ronda o quadrante nobre. E a **Argentina 2022** confirma o título com eficiência ofensiva real, não inflada.

## Os números por trás

```sql table_perf
select
    team as "Seleção",
    year as "Edição",
    matches as "Jogos",
    goals_for as "GP",
    goals_against as "GC",
    attack_vs_xg as "Ataque vs xG",
    defense_vs_xg as "Defesa vs xG"
from copa.team_performance
where matches >= 5
order by (attack_vs_xg + defense_vs_xg) desc
```

<DataTable data={table_perf} rows=12 search=true/>

---

Da eficiência individual, o desk vira a atenção para a pergunta que nenhum ranking responde: **[o paradoxo do favorito](/favorito)** — se as seleções mais fortes vencem tanto por jogo, por que o número 1 nunca levanta a taça?
