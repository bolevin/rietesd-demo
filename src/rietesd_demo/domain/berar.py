"""Berar's correction for e.s.d.'s underestimated by local correlations.

J.-F. Berar & P. Lelann, J. Appl. Cryst. 24 (1991) 1-5.

Least squares assumes independent residuals.  In a Rietveld fit they are not:
a misfitted peak leaves a run of neighbouring points that all err the same way,
and the e.s.d.'s the refinement prints come out too small.  Berar and Lelann
re-estimate the sum of squares with every such run counted as (partly) one
observation; the square root of the ratio of the two sums is the factor the
e.s.d.'s have to be multiplied by.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

#: The reference program (RietESD, QBASIC) uses this truncated value, and so does
#: the demo.  math.pi would move the coefficient by about 4e-8 (relative) - less
#: than the single-precision reference can resolve.
PI_AS_IN_REFERENCE = 3.14159


def esd_coefficient(residuals: Sequence[float], sigmas: Sequence[float]) -> float:
    """Factor by which the refinement's e.s.d.'s should be multiplied (>= 0).

    ``residuals`` are Yobs - Ycalc, ``sigmas`` the standard uncertainties of the
    points, both in scan order.  Returns 0 when every residual is zero.

    The loop follows the reference implementation statement by statement,
    including its use of the *previous* point's sigma for both members of a
    correlated pair; the result is pinned by a golden-master test.
    """
    plain_sum = 0.0  # sum of r^2 / sigma^2, every point independent
    corrected_sum = 0.0  # the same with correlated runs merged
    run = 0.0  # correlated part carried along the current run
    in_run = False
    previous = 0.0  # residual of the previous point
    previous_sigma = 1.0

    for residual, sigma in zip(residuals, sigmas, strict=True):
        plain_sum += residual**2 / sigma**2

        if residual * previous > 0.0:  # same sign as its neighbour
            if not in_run:
                in_run = True
                corrected_sum += run * run
                run = 0.0
            earlier = previous**2 / previous_sigma**2
            current = residual**2 / previous_sigma**2
            p = math.sqrt(2.0 * PI_AS_IN_REFERENCE * (current + earlier))
            p = p / (2.0 + p)  # probability the two are linked
            run += p * math.sqrt(earlier)
            corrected_sum += (1.0 - p * p) * earlier
        else:  # sign change closes the run
            corrected_sum += run * run
            run = abs(previous) / previous_sigma
            in_run = False

        previous, previous_sigma = residual, sigma

    corrected_sum += run * run
    if plain_sum == 0.0:
        return 0.0
    return math.sqrt(corrected_sum / plain_sum)
