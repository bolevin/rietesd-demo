from __future__ import annotations

import pytest

from rietesd_demo.domain import (
    AnalysisSettings,
    Correlation,
    InsufficientDataError,
    Pattern,
    analyse,
)


def test_tiny_pattern_end_to_end(tiny: Pattern) -> None:
    result = analyse(tiny, AnalysisSettings(n_parameters=1))
    # weighted residuals are 1, -1, -1, 1: d = (4 + 0 + 4) / 4
    assert result.durbin_watson == pytest.approx(2.0)
    assert result.n_points == 4
    assert result.two_theta_range == (10.0, 10.3)
    assert result.factors.r_wp == pytest.approx(8.0)


def test_window_restricts_every_statistic(sample: Pattern) -> None:
    whole = analyse(sample, AnalysisSettings(27, 2))
    part = analyse(sample, AnalysisSettings(27, 2, two_theta_min=20.0, two_theta_max=60.0))
    assert part.n_points == 2001
    assert part.two_theta_range == (20.0, 60.0)
    assert part.factors.r_wp != whole.factors.r_wp
    assert part.esd_coefficient != whole.esd_coefficient


def test_sample_needs_the_correction(sample: Pattern) -> None:
    result = analyse(sample, AnalysisSettings(27, 2))
    assert result.correlation is Correlation.POSITIVE
    assert result.esd_need_correction
    assert result.esd_coefficient > 1.0


def test_too_few_points_in_the_window(sample: Pattern) -> None:
    settings = AnalysisSettings(two_theta_min=10.0, two_theta_max=10.02)
    with pytest.raises(InsufficientDataError, match="Only 2 data point"):
        analyse(sample, settings)


def test_more_parameters_than_points(tiny: Pattern) -> None:
    with pytest.raises(InsufficientDataError, match=r"N - P \+ C = -1"):
        analyse(tiny, AnalysisSettings(n_parameters=5))


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n_parameters": -1}, "must not be negative"),
        ({"n_parameters": 2, "n_constraints": 3}, "C cannot exceed P"),
        ({"two_theta_min": 50.0, "two_theta_max": 40.0}, "window is empty"),
    ],
)
def test_settings_validate_themselves(kwargs: dict[str, float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        AnalysisSettings(**kwargs)  # type: ignore[arg-type]
