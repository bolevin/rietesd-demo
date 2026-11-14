from __future__ import annotations

import math

import pytest

from rietesd_demo.domain import Correlation, InsufficientDataError, WeightScheme
from rietesd_demo.domain.statistics import classify, critical_value, durbin_watson


def test_alternating_residuals_give_d_near_four() -> None:
    # differences are all 2, so the numerator is 3 * 4 and the denominator 4
    assert durbin_watson([1.0, -1.0, 1.0, -1.0]) == pytest.approx(3.0)


def test_constant_residuals_give_d_of_zero() -> None:
    assert durbin_watson([2.0, 2.0, 2.0]) == 0.0


def test_perfect_fit_has_no_statistic() -> None:
    with pytest.raises(InsufficientDataError, match="undefined"):
        durbin_watson([0.0, 0.0, 0.0])


def test_critical_value_by_hand() -> None:
    expected = 2.0 * (99.0 / 92.0 - 3.0902 / math.sqrt(102.0))
    assert critical_value(100, 10, 2) == pytest.approx(expected, rel=1e-15)


def test_critical_value_needs_free_points() -> None:
    with pytest.raises(InsufficientDataError, match=r"N - P \+ C = 0"):
        critical_value(10, 12, 2)


@pytest.mark.parametrize(
    ("d", "verdict"),
    [
        (1.0, Correlation.POSITIVE),
        (1.9, Correlation.NONE),  # exactly Q: not below it
        (2.1, Correlation.NONE),  # exactly 4 - Q: not above it
        (3.0, Correlation.NEGATIVE),
    ],
)
def test_classification_boundaries(d: float, verdict: Correlation) -> None:
    assert classify(d, q=1.9) is verdict


def test_weight_schemes() -> None:
    assert WeightScheme.INVERSE_INTENSITY.weight(400.0) == pytest.approx(1 / 400)
    assert WeightScheme.INVERSE_INTENSITY.sigma(400.0) == pytest.approx(20.0)
    assert WeightScheme.INVERSE_SQRT_INTENSITY.weight(400.0) == pytest.approx(1 / 20)
    assert WeightScheme.INVERSE_SQRT_INTENSITY.sigma(400.0) == pytest.approx(math.sqrt(20))


@pytest.mark.parametrize("scheme", list(WeightScheme))
def test_zero_counts_weigh_as_one_count(scheme: WeightScheme) -> None:
    assert scheme.weight(0.0) == scheme.weight(1.0) == 1.0
