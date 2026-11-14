"""A powder-diffraction pattern after a Rietveld refinement."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

from rietesd_demo.domain.errors import InvalidPatternError


@dataclass(frozen=True, slots=True)
class Pattern:
    """Observed and calculated intensities on a common 2-theta grid.

    The four columns are parallel: one entry per measured point.  A pattern is
    valid by construction - every instance has passed the checks below, so the
    calculation never has to defend itself against a ragged or non-finite input.
    """

    two_theta: tuple[float, ...]
    y_obs: tuple[float, ...]
    y_calc: tuple[float, ...]
    background: tuple[float, ...]
    title: str = ""

    def __post_init__(self) -> None:
        n = len(self.two_theta)
        columns = {"Yobs": self.y_obs, "Ycalc": self.y_calc, "Bkg": self.background}
        for name, column in columns.items():
            if len(column) != n:
                raise InvalidPatternError(
                    f"Column {name} has {len(column)} values, 2Theta has {n}."
                )
        if n == 0:
            raise InvalidPatternError("The pattern holds no data points.")
        for name, column in {"2Theta": self.two_theta, **columns}.items():
            if not all(math.isfinite(v) for v in column):
                raise InvalidPatternError(f"Column {name} holds a value that is not a number.")
        if any(b <= a for a, b in pairwise(self.two_theta)):
            raise InvalidPatternError("2Theta must increase from point to point.")
        if any(y < 0.0 for y in self.y_obs):
            raise InvalidPatternError("Observed intensities must not be negative.")

    def __len__(self) -> int:
        return len(self.two_theta)

    @property
    def difference(self) -> tuple[float, ...]:
        """Yobs - Ycalc for every point."""
        return tuple(o - c for o, c in zip(self.y_obs, self.y_calc, strict=True))

    def window(self, low: float | None, high: float | None) -> Pattern:
        """The part of the pattern with ``low <= 2Theta <= high`` (None = open end)."""
        lo = -math.inf if low is None else low
        hi = math.inf if high is None else high
        keep = [i for i, t in enumerate(self.two_theta) if lo <= t <= hi]
        if not keep:
            raise InvalidPatternError(f"No data points between 2Theta = {lo:g} and {hi:g} degrees.")
        first, last = keep[0], keep[-1] + 1
        return Pattern(
            two_theta=self.two_theta[first:last],
            y_obs=self.y_obs[first:last],
            y_calc=self.y_calc[first:last],
            background=self.background[first:last],
            title=self.title,
        )
