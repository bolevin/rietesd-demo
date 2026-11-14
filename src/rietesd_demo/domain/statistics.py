"""Serial correlation of the residuals: the Durbin-Watson test.

R. J. Hill & H. D. Flack, J. Appl. Cryst. 20 (1987) 356-361.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from enum import Enum
from itertools import pairwise

from rietesd_demo.domain.errors import InsufficientDataError

#: 0.1 % point of the standard normal distribution, as used by Hill & Flack.
NORMAL_QUANTILE_0_1_PERCENT = 3.0902


class Correlation(Enum):
    """Verdict of the Durbin-Watson test at the 0.1 % significance level."""

    POSITIVE = "positive serial correlation"
    NONE = "no serial correlation"
    NEGATIVE = "negative serial correlation"


def durbin_watson(weighted_residuals: Sequence[float]) -> float:
    """d = sum (r_i - r_{i-1})^2 / sum r_i^2, with r_i = (Yobs_i - Ycalc_i) / sigma_i.

    d is 2 for uncorrelated residuals, falls towards 0 when neighbours share
    their sign and rises towards 4 when they alternate.
    """
    denominator = math.fsum(r * r for r in weighted_residuals)
    if denominator == 0.0:
        raise InsufficientDataError(
            "Ycalc equals Yobs at every point, so the Durbin-Watson statistic is undefined."
        )
    numerator = math.fsum((b - a) ** 2 for a, b in pairwise(weighted_residuals))
    return numerator / denominator


def critical_value(n_points: int, n_parameters: int, n_constraints: int) -> float:
    """Q: residuals are serially correlated when d < Q or d > 4 - Q."""
    degrees_of_freedom = n_points - n_parameters + n_constraints
    if degrees_of_freedom <= 0:
        raise InsufficientDataError(
            f"N - P + C = {degrees_of_freedom}: the pattern has no more points "
            "than the refinement has free parameters."
        )
    ratio = (n_points - 1) / degrees_of_freedom
    return 2.0 * (ratio - NORMAL_QUANTILE_0_1_PERCENT / math.sqrt(n_points + 2))


def classify(d: float, q: float) -> Correlation:
    if d < q:
        return Correlation.POSITIVE
    if d > 4.0 - q:
        return Correlation.NEGATIVE
    return Correlation.NONE
