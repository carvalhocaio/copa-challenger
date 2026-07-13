"""Testes do bootstrap de intervalo de confiança do backtest (Missão 04)."""

from copa_challenger.predict.evaluate import bootstrap_cis

# Métrica por jogo (0/1 de acerto): média = 0.6.
_ACC = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]


def test_bootstrap_is_deterministic_given_seed() -> None:
    a = bootstrap_cis({"acc": _ACC}, n_resamples=500, seed=42)
    b = bootstrap_cis({"acc": _ACC}, n_resamples=500, seed=42)
    assert a == b


def test_bootstrap_ci_brackets_point_estimate() -> None:
    mean = sum(_ACC) / len(_ACC)
    lo, hi = bootstrap_cis({"acc": _ACC}, n_resamples=1000, seed=7)["acc"]
    assert lo <= mean <= hi
    assert lo < hi


def test_bootstrap_shared_indices_across_metrics() -> None:
    # Duas métricas idênticas devem produzir intervalos idênticos, pois os
    # índices reamostrados são compartilhados por reamostragem.
    result = bootstrap_cis({"a": _ACC, "b": list(_ACC)}, n_resamples=300, seed=3)
    assert result["a"] == result["b"]
