"""The factors on four points, every sum worked out by hand.

Yobs = 100, 400, 100, 25; Ycalc = 90, 420, 110, 20; Bkg = 20 throughout.
With w = 1/Yobs every point contributes w * diff^2 = 1, so chi^2 = 4, and
sum(w * Yobs^2) = sum(Yobs) = 625.
"""

from __future__ import annotations

import math

import pytest

from rietesd_demo.domain import InsufficientDataError, Pattern, WeightScheme
from rietesd_demo.domain.agreement import agreement_factors


def test_factors_by_hand(tiny: Pattern) -> None:
    f = agreement_factors(tiny, WeightScheme.INVERSE_INTENSITY, degrees_of_freedom=3)
    assert f.r_wp == pytest.approx(8.0)
    assert f.r_exp == pytest.approx(100.0 * math.sqrt(3.0 / 625.0))
    assert f.gof == pytest.approx(math.sqrt(4.0 / 3.0))
    assert f.r_p == pytest.approx(7.2)  # 45 / 625
    # net intensities 80, 380, 80, 5: sum(w * net^2) = 64 + 361 + 64 + 1
    assert f.r_wp_bkg == pytest.approx(100.0 * math.sqrt(4.0 / 490.0))
    assert f.r_exp_bkg == pytest.approx(100.0 * math.sqrt(3.0 / 490.0))
    assert f.r_p_bkg == pytest.approx(100.0 * 45.0 / 545.0)


def test_goodness_of_fit_is_rwp_over_rexp(tiny: Pattern) -> None:
    for scheme in WeightScheme:
        f = agreement_factors(tiny, scheme, degrees_of_freedom=3)
        assert f.gof == pytest.approx(f.r_wp / f.r_exp)
        assert f.gof == pytest.approx(f.r_wp_bkg / f.r_exp_bkg)


def test_background_correction_raises_the_factors(tiny: Pattern) -> None:
    f = agreement_factors(tiny, WeightScheme.INVERSE_INTENSITY, degrees_of_freedom=3)
    assert f.r_wp_bkg > f.r_wp
    assert f.r_p_bkg > f.r_p


def test_no_free_points_is_refused(tiny: Pattern) -> None:
    with pytest.raises(InsufficientDataError, match=r"N - P \+ C = 0"):
        agreement_factors(tiny, WeightScheme.INVERSE_INTENSITY, degrees_of_freedom=0)


def test_pattern_that_is_all_background_is_refused() -> None:
    flat = Pattern((1.0, 2.0, 3.0), (5.0, 5.0, 5.0), (4.0, 6.0, 5.0), (5.0, 5.0, 5.0))
    with pytest.raises(InsufficientDataError, match="background equals Yobs"):
        agreement_factors(flat, WeightScheme.INVERSE_INTENSITY, degrees_of_freedom=2)
