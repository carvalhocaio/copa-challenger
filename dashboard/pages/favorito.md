---
title: O paradoxo do favorito
description: Por que o ranking FIFA acerta o jogo mas erra o campeão
---

_Desde que o ranking FIFA existe (1992), **o número 1 nunca venceu uma Copa**. Não é azar repetido — é matemática. Este é o paradoxo que fecha o desk._

## O ranking acerta — mais do que se imagina

A intuição popular diz que "Copa do Mundo é uma caixinha de surpresas" e que o ranking pouco vale. Os dados de 2022 dizem o contrário: por **partida isolada**, a seleção mais bem ranqueada venceu na maioria das vezes — e foi ainda mais confiável no mata-mata do que na fase de grupos.

```sql favorite
select
    round,
    stage_order,
    decided,
    favorite_wins,
    favorite_win_pct
from copa.favorite_by_round
order by stage_order
```

<BarChart
    data={favorite}
    x=round
    y=favorite_win_pct
    sort=false
    title="Vitória do favorito por fase — Catar 2022"
    subtitle="% das partidas decididas em que a seleção mais bem ranqueada venceu"
    yAxisTitle="% vitória do favorito"
    yMax=100
    labels=true
/>

<Note>
Amostra de uma única edição (2022 é a única com snapshot de ranking no dataset). As fases finais têm poucos jogos — Semifinal, Disputa de 3º e Final somam 4 partidas. Leia a tendência como **indício**, não prova. O número acima de cada barra é o total de jogos daquela fase.
</Note>

## Então por que o favorito não leva a taça?

Porque vencer uma Copa não é vencer **um** jogo — é vencer **sete seguidos**. E probabilidade não se soma, se multiplica.

Suponha um favorito muito forte, que ganha **81%** das partidas de mata-mata (a taxa observada em 2022). Parece dominante. Mas a chance de emendar os sete confrontos que separam a estreia do título é:

<p style="text-align: center; font-size: 1.25rem;">0,81⁷ ≈ 0,23</p>

**Cerca de 23%.** Ou seja: mesmo o favorito mais confiável do torneio tem ~1 em 4 de "correr a tabela" — e ainda por cima costuma pegar o chaveamento mais duro. Some a isso o fato de que *vários* times chegam fortes, e a probabilidade de que **algum** favorito tropece em algum jogo vira quase certeza estatística.

```sql compounding
select 1 as jogos, 0.81 as prob_titulo union all
select 2, 0.81*0.81 union all
select 3, pow(0.81, 3) union all
select 4, pow(0.81, 4) union all
select 5, pow(0.81, 5) union all
select 6, pow(0.81, 6) union all
select 7, pow(0.81, 7)
order by jogos
```

<LineChart
    data={compounding}
    x=jogos
    y=prob_titulo
    title="A erosão do favorito"
    subtitle="Probabilidade de vencer N jogos seguidos, cada um a 81%"
    xAxisTitle="Jogos consecutivos vencidos"
    yAxisTitle="Probabilidade acumulada"
    yFmt=pct0
    labels=true
/>

O ranking, portanto, **prevê bem o confronto e mal a sequência**. Ele mede força relativa num jogo — não a resistência a sete eliminatórias de mata-mata, onde um erro basta.

## O amplificador do azar: os pênaltis

Se o mata-mata é onde o favorito pode cair, a disputa por pênaltis é o mecanismo mais cruel disso — um empate que zera o histórico técnico e entrega o jogo à loteria dos 11 metros. Foram **9 disputas** em 2018 e 2022, e um nome as domina.

```sql shootouts
select
    year as "Edição",
    round as "Fase",
    home_team || ' × ' || away_team as "Confronto",
    winner as "Avançou"
from copa.shootouts
order by year, stage_order
```

<DataTable data={shootouts} rows=9/>

A **Croácia aparece em 4 das 9** — Dinamarca e Rússia em 2018, Japão e Brasil em 2022. As campanhas de vice (2018) e semifinal (2022) não foram construídas apesar dos pênaltis: foram construídas **neles**. É o retrato vivo da tese — um time que perdeu quase toda disputa de força pura no xG (a Croácia 2022 tem `attack_vs_xg` negativo) e mesmo assim foi longe, porque o mata-mata premia quem sobrevive, não quem domina.

## O que o desk conclui

Três atos, uma leitura: **as duas Copas** mostraram que eficiência vence volume; o **paradoxo do favorito** mostrou que força relativa não resiste à composição de sete jogos; e os **pênaltis** mostraram que o formato mata-mata é, por desenho, um amplificador de variância.

Para uma comissão técnica, a lição não é "ignore o ranking" — é **"o ranking te leva às oitavas; o título exige eficiência de finalização e resiliência no detalhe, não posição na tabela"**. É por isso que o Catar coroou Argentina e França, e não os dois primeiros do ranking. E é por isso que, provavelmente, o nº 1 seguirá esperando.
