"""Properties that must hold for every pattern, not only for the examples."""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from rietesd_demo.domain import AnalysisSettings, Pattern, WeightScheme, analyse

_counts = st.floats(min_value=1.0, max_value=1e6, allow_nan=False)
_point = st.tuples(_counts, _counts, st.floats(min_value=0.0, max_value=0.9))
_schemes = st.sampled_from(list(WeightScheme))


def _pattern(points: list[tuple[float, float, float]], scale: float = 1.0) -> Pattern:
    return Pattern(
        two_theta=tuple(10.0 + 0.02 * i for i in range(len(points))),
        y_obs=tuple(scale * obs for obs, _, _ in points),
        y_calc=tuple(scale * calc for _, calc, _ in points),
        # background as a fraction of Yobs, so Yobs - Bkg never vanishes
        background=tuple(scale * obs * fraction for obs, _, fraction in points),
    )


@st.composite
def patterns(draw: st.DrawFn) -> list[tuple[float, float, float]]:
    points = draw(st.lists(_point, min_size=4, max_size=60))
    assume(any(obs != calc for obs, calc, _ in points))
    return points


@given(patterns(), _schemes)
def test_durbin_watson_lies_between_zero_and_four(
    points: list[tuple[float, float, float]], scheme: WeightScheme
) -> None:
    result = analyse(_pattern(points), AnalysisSettings(weighting=scheme))
    assert 0.0 <= result.durbin_watson <= 4.0


@given(patterns(), _schemes)
def test_coefficient_and_factors_are_not_negative(
    points: list[tuple[float, float, float]], scheme: WeightScheme
) -> None:
    result = analyse(_pattern(points), AnalysisSettings(weighting=scheme))
    f = result.factors
    assert result.esd_coefficient >= 0.0
    assert min(f.r_wp, f.r_exp, f.gof, f.r_p, f.r_wp_bkg, f.r_exp_bkg, f.r_p_bkg) >= 0.0
    assert f.r_wp_bkg >= f.r_wp * (1.0 - 1e-12)  # a smaller denominator


@given(patterns(), _schemes, st.floats(min_value=1.0, max_value=1e3))
@settings(max_examples=200)
def test_counting_time_does_not_change_the_r_factors(
    points: list[tuple[float, float, float]], scheme: WeightScheme, scale: float
) -> None:
    """Measuring k times longer multiplies every intensity by k.  The R-factors
    and the Durbin-Watson statistic are ratios and must not notice."""
    short = analyse(_pattern(points), AnalysisSettings(weighting=scheme))
    long = analyse(_pattern(points, scale), AnalysisSettings(weighting=scheme))
    assert long.durbin_watson == pytest.approx(short.durbin_watson, rel=1e-9, abs=1e-12)
    assert long.factors.r_wp == pytest.approx(short.factors.r_wp, rel=1e-9)
    assert long.factors.r_p == pytest.approx(short.factors.r_p, rel=1e-9)
    assert long.factors.r_wp_bkg == pytest.approx(short.factors.r_wp_bkg, rel=1e-9)
