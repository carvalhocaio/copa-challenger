"""Modelo de gols esperados e probabilidades W/D/L.

Duas peças: (1) um fallback linear (força ~ pontos FIFA) para seleções sem
histórico em 2018/2022, treinado só nas que têm os dois dados; (2) um
modelo de Poisson simples (calculado à mão, sem scipy) que converte gols
esperados de cada lado em probabilidade de vitória/empate/derrota.

Sem vantagem de mando: raw.schedule_2026 não distingue jogo em sede real de
jogo em sede neutra (coluna Notes vem 100% nula), então os 72 jogos do
grupo são tratados como neutros — é a opção honesta com os dados que existem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import polars as pl

# bounds observados no histórico real (força sem shrinkage); protegem o
# fallback contra extrapolação absurda em seleções de ranking muito extremo.
ATTACK_CLIP = (0.4, 1.6)
DEFENSE_CLIP = (0.5, 2.0)


@dataclass(frozen=True)
class FallbackFit:
    attack_intercept: float
    attack_slope: float
    defense_intercept: float
    defense_slope: float


def fit_fallback(features: pl.DataFrame) -> FallbackFit:
    """Regressão linear (grau 1) de attack/defense em função dos pontos FIFA,
    usando só as seleções com histórico (attack/defense não nulos)."""
    known = features.filter(pl.col("attack").is_not_null() & pl.col("points").is_not_null())
    points = known["points"].to_numpy()

    attack_slope, attack_intercept = np.polyfit(points, known["attack"].to_numpy(), 1)
    defense_slope, defense_intercept = np.polyfit(points, known["defense"].to_numpy(), 1)

    return FallbackFit(
        attack_intercept=float(attack_intercept),
        attack_slope=float(attack_slope),
        defense_intercept=float(defense_intercept),
        defense_slope=float(defense_slope),
    )


def apply_fallback(features: pl.DataFrame, fit: FallbackFit) -> pl.DataFrame:
    """Preenche attack/defense nulos (seleções sem histórico) a partir dos
    pontos FIFA e do fit. Não altera quem já tem histórico."""
    points = pl.col("points")
    predicted_attack = (fit.attack_intercept + fit.attack_slope * points).clip(*ATTACK_CLIP)
    predicted_defense = (fit.defense_intercept + fit.defense_slope * points).clip(*DEFENSE_CLIP)
    return features.with_columns(
        pl.coalesce(pl.col("attack"), predicted_attack).alias("attack"),
        pl.coalesce(pl.col("defense"), predicted_defense).alias("defense"),
    )


def expected_goals(attack_i: float, defense_j: float, league_avg: float) -> float:
    """Gols esperados do time i, dado seu ataque e a defesa do adversário j."""
    return league_avg * attack_i * defense_j


def poisson_pmf(k: int, mu: float) -> float:
    return math.exp(-mu) * mu**k / math.factorial(k)


def match_outcome_probs(
    mu_home: float, mu_away: float, max_goals: int = 8
) -> tuple[float, float, float]:
    """Probabilidade (vitória mandante, empate, vitória visitante), assumindo
    gols de cada lado independentes e Poisson. A grade é truncada em
    max_goals e renormalizada (resíduo de cauda é desprezível para mu típico
    de futebol)."""
    home_pmf = [poisson_pmf(k, mu_home) for k in range(max_goals + 1)]
    away_pmf = [poisson_pmf(k, mu_away) for k in range(max_goals + 1)]

    prob_home_win = prob_draw = prob_away_win = 0.0
    for i, p_home in enumerate(home_pmf):
        for j, p_away in enumerate(away_pmf):
            joint = p_home * p_away
            if i > j:
                prob_home_win += joint
            elif i == j:
                prob_draw += joint
            else:
                prob_away_win += joint

    total = prob_home_win + prob_draw + prob_away_win
    return prob_home_win / total, prob_draw / total, prob_away_win / total
