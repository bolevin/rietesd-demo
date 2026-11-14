from __future__ import annotations

import math

import pytest

from rietesd_demo.domain import InvalidPatternError, Pattern


def make(**overrides: tuple[float, ...]) -> Pattern:
    columns: dict[str, tuple[float, ...]] = {
        "two_theta": (1.0, 2.0, 3.0),
        "y_obs": (10.0, 20.0, 30.0),
        "y_calc": (11.0, 19.0, 30.0),
        "background": (1.0, 1.0, 1.0),
    }
    columns.update(overrides)
    return Pattern(columns["two_theta"], columns["y_obs"], columns["y_calc"], columns["background"])


def test_difference_is_observed_minus_calculated() -> None:
    assert make().difference == (-1.0, 1.0, 0.0)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"y_calc": (1.0, 2.0)}, "Ycalc has 2 values"),
        ({"background": (1.0, math.nan, 1.0)}, "Bkg holds a value that is not a number"),
        ({"y_obs": (1.0, math.inf, 1.0)}, "Yobs holds a value that is not a number"),
        ({"two_theta": (1.0, 1.0, 2.0)}, "2Theta must increase"),
        ({"two_theta": (3.0, 2.0, 1.0)}, "2Theta must increase"),
        ({"y_obs": (1.0, -0.5, 1.0)}, "must not be negative"),
    ],
)
def test_malformed_patterns_are_refused(
    overrides: dict[str, tuple[float, ...]], message: str
) -> None:
    with pytest.raises(InvalidPatternError, match=message):
        make(**overrides)


def test_empty_pattern_is_refused() -> None:
    with pytest.raises(InvalidPatternError, match="no data points"):
        Pattern((), (), (), ())


def test_window_keeps_both_ends() -> None:
    cut = make().window(2.0, 3.0)
    assert cut.two_theta == (2.0, 3.0)
    assert cut.y_obs == (20.0, 30.0)


def test_open_window_is_the_whole_pattern() -> None:
    pattern = make()
    assert pattern.window(None, None) == pattern


def test_window_without_points_is_refused() -> None:
    with pytest.raises(InvalidPatternError, match="No data points between"):
        make().window(5.0, 6.0)
