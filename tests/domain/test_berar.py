from __future__ import annotations

import math

import pytest

from rietesd_demo.domain.berar import PI_AS_IN_REFERENCE, esd_coefficient


def test_alternating_residuals_are_not_merged() -> None:
    # No two neighbours share a sign, so every point counts on its own - except
    # the last one, which the reference algorithm adds only when a successor
    # arrives.  Corrected sum 9 + 1 + 4 + 16 = 30, plain sum 31.
    residuals = [3.0, -1.0, 2.0, -4.0, 1.0]
    got = esd_coefficient(residuals, [1.0] * 5)
    assert got == pytest.approx(math.sqrt(30.0 / 31.0), rel=1e-14)


def test_uncorrelated_noise_needs_almost_no_correction() -> None:
    residuals = [1.0 if i % 2 else -1.0 for i in range(2000)]
    assert esd_coefficient(residuals, [1.0] * 2000) == pytest.approx(1.0, abs=1e-3)


def test_a_run_of_same_sign_residuals_raises_the_coefficient() -> None:
    residuals = [2.0] * 50
    assert esd_coefficient(residuals, [1.0] * 50) > 1.5


def test_perfect_fit_returns_zero() -> None:
    assert esd_coefficient([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]) == 0.0


def _link(earlier: float, current: float) -> float:
    p = math.sqrt(2.0 * PI_AS_IN_REFERENCE * (earlier + current))
    return p / (2.0 + p)


def test_three_point_run_by_hand() -> None:
    """Follow the algorithm on paper for residuals 3, 4, 5, -1 with sigma = 1.

    Points 1-3 form a run, point 4 closes it.  With p1 and p2 the linking
    probabilities of the two pairs, the run contributes
    9 (1 - p1^2) + 16 (1 - p2^2) + (3 p1 + 4 p2)^2, and the point that closed
    it 25.  The very last point enters the plain sum only - the reference
    algorithm counts a point when its successor arrives.
    """
    p1, p2 = _link(9.0, 16.0), _link(16.0, 25.0)
    corrected = 9.0 * (1 - p1 * p1) + 16.0 * (1 - p2 * p2) + (3 * p1 + 4 * p2) ** 2 + 25.0
    plain = 9.0 + 16.0 + 25.0 + 1.0
    got = esd_coefficient([3.0, 4.0, 5.0, -1.0], [1.0] * 4)
    assert got == pytest.approx(math.sqrt(corrected / plain), rel=1e-14)
    assert got > 1.0


def test_a_pair_alone_is_not_a_run() -> None:
    # for two points the merged and the independent estimate coincide:
    # 9 (1 - p^2) + (3 p)^2 = 9
    got = esd_coefficient([3.0, 4.0, -1.0], [1.0] * 3)
    assert got == pytest.approx(math.sqrt(25.0 / 26.0), rel=1e-14)


def test_sigma_scales_the_residuals() -> None:
    # (residual, sigma) = (6, 2) is the same observation as (3, 1)
    a = esd_coefficient([6.0, 8.0, 10.0, -2.0], [2.0] * 4)
    b = esd_coefficient([3.0, 4.0, 5.0, -1.0], [1.0] * 4)
    assert a == pytest.approx(b, rel=1e-14)
