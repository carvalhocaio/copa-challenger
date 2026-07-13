"""Testes do núcleo matemático do pipeline preditivo (Missão 04)."""

import math

import polars as pl
import pytest

from copa_challenger.predict.features import strength_from_stats
from copa_challenger.predict.model import (
    ATTACK_CLIP,
    DEFENSE_CLIP,
    FallbackFit,
    apply_fallback,
    fit_fallback,
    match_outcome_probs,
    poisson_pmf,
)


@pytest.mark.parametrize("mu", [0.5, 1.323, 2.8, 5.0])
def test_poisson_pmf_sums_to_one(mu: float) -> None:
    total = sum(poisson_pmf(k, mu) for k in range(30))
    assert total == pytest.approx(1.0, abs=1e-6)


def test_match_outcome_probs_symmetric_when_strengths_equal() -> None:
    prob_home, prob_draw, prob_away = match_outcome_probs(1.5, 1.5)
    assert prob_home == pytest.approx(prob_away, abs=1e-9)
    assert prob_home + prob_draw + prob_away == pytest.approx(1.0, abs=1e-9)


def test_match_outcome_probs_favors_stronger_side() -> None:
    prob_home, _, prob_away = match_outcome_probs(2.5, 0.8)
    assert prob_home > prob_away


def test_shrinkage_pulls_small_samples_harder_toward_average() -> None:
    # mesma taxa bruta (attack "verdadeiro" = 1.5x a média), mas Panama jogou
    # 3 partidas e Argentina jogou 12 — o shrinkage deve puxar Panama mais
    # forte em direção a 1.0.
    df = pl.DataFrame({
        "team": ["Panama", "Argentina"],
        "matches": [3.0, 12.0],
        "goals_for": [4.5, 18.0],
        "goals_against": [3.0, 12.0],
        "xg_for": [4.5, 18.0],
        "xg_against": [3.0, 12.0],
    })
    out = strength_from_stats(df, league_avg=1.0, k=3.0)
    panama = out.filter(pl.col("team") == "Panama")["attack"].item()
    argentina = out.filter(pl.col("team") == "Argentina")["attack"].item()
    assert abs(panama - 1.0) < abs(argentina - 1.0)


@pytest.mark.parametrize(
    ("blend_weight", "expected_attack"),
    [(1.0, 2.0), (0.0, 1.0), (0.5, 1.5)],
)
def test_blend_weight_mixes_goals_and_xg(blend_weight: float, expected_attack: float) -> None:
    # 1 jogo, k=0 (sem shrinkage), league_avg=1 -> attack = blend do ataque:
    # w*gol + (1-w)*xg com gol=2.0 e xg=1.0. w=1 usa só gol, w=0 só xg, w=0.5 a média.
    df = pl.DataFrame({
        "team": ["T"],
        "matches": [1.0],
        "goals_for": [2.0],
        "goals_against": [2.0],
        "xg_for": [1.0],
        "xg_against": [1.0],
    })
    out = strength_from_stats(df, league_avg=1.0, k=0.0, blend_weight=blend_weight)
    assert out["attack"].item() == pytest.approx(expected_attack)


def test_fit_fallback_recovers_linear_relationship() -> None:
    points = [500.0, 1000.0, 1500.0, 2000.0]
    features = pl.DataFrame({
        "team": [f"team_{i}" for i in range(4)],
        "points": points,
        "attack": [0.5 + 0.0004 * p for p in points],
        "defense": [1.5 - 0.0002 * p for p in points],
    })
    fit = fit_fallback(features)
    assert fit.attack_slope == pytest.approx(0.0004, abs=1e-6)
    assert fit.attack_intercept == pytest.approx(0.5, abs=1e-3)
    assert fit.defense_slope == pytest.approx(-0.0002, abs=1e-6)
    assert fit.defense_intercept == pytest.approx(1.5, abs=1e-3)


def test_apply_fallback_only_fills_missing_history() -> None:
    features = pl.DataFrame({
        "team": ["HasHistory", "ColdStart"],
        "points": [1800.0, 1800.0],
        "attack": [1.2, None],
        "defense": [0.9, None],
    })
    fit = FallbackFit(
        attack_intercept=0.5, attack_slope=0.0001, defense_intercept=1.0, defense_slope=-0.0001
    )

    out = apply_fallback(features, fit)

    assert out.filter(pl.col("team") == "HasHistory")["attack"].item() == pytest.approx(1.2)
    assert out.filter(pl.col("team") == "HasHistory")["defense"].item() == pytest.approx(0.9)

    filled_attack = out.filter(pl.col("team") == "ColdStart")["attack"].item()
    filled_defense = out.filter(pl.col("team") == "ColdStart")["defense"].item()
    expected_attack = fit.attack_intercept + fit.attack_slope * 1800.0
    expected_defense = fit.defense_intercept + fit.defense_slope * 1800.0
    assert filled_attack == pytest.approx(expected_attack)
    assert filled_defense == pytest.approx(expected_defense)


def test_apply_fallback_respects_clip_bounds() -> None:
    features = pl.DataFrame({
        "team": ["ExtremeHigh", "ExtremeLow"],
        "points": [3000.0, -3000.0],
        "attack": [None, None],
        "defense": [None, None],
    })
    fit = FallbackFit(
        attack_intercept=0.5, attack_slope=0.001, defense_intercept=1.0, defense_slope=0.001
    )

    out = apply_fallback(features, fit)

    assert ATTACK_CLIP[0] <= out["attack"].min() and out["attack"].max() <= ATTACK_CLIP[1]
    assert DEFENSE_CLIP[0] <= out["defense"].min() and out["defense"].max() <= DEFENSE_CLIP[1]
    assert not math.isnan(out["attack"].min())
