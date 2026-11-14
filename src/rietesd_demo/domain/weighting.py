"""Weighting schemes: how much each point counts in the least-squares sums."""

from __future__ import annotations

import math
from enum import Enum

#: A point with zero counts would get an infinite weight.  Like the reference
#: program, the calculation treats it as one count instead.
MIN_COUNTS = 1.0


def counts(y_obs: float) -> float:
    """The intensity the weights are computed from (zero counts -> one count)."""
    return y_obs if y_obs > 0.0 else MIN_COUNTS


class WeightScheme(Enum):
    """The weight w of a point as a function of its observed intensity.

    Adding a scheme means adding a member and one branch in :meth:`weight`;
    everything downstream (Durbin-Watson, Berar, agreement factors) goes through
    :meth:`weight` and :meth:`sigma` and needs no change.
    """

    INVERSE_INTENSITY = "1/Yobs"
    INVERSE_SQRT_INTENSITY = "1/sqrt(Yobs)"

    def weight(self, y_obs: float) -> float:
        y = counts(y_obs)
        if self is WeightScheme.INVERSE_SQRT_INTENSITY:
            return 1.0 / math.sqrt(y)
        return 1.0 / y

    def sigma(self, y_obs: float) -> float:
        """Standard uncertainty of the point, sigma = 1/sqrt(w)."""
        return math.sqrt(1.0 / self.weight(y_obs))
