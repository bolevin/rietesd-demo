"""Agreement factors of a Rietveld refinement (R-factors and goodness of fit)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from rietesd_demo.domain.errors import InsufficientDataError
from rietesd_demo.domain.pattern import Pattern
from rietesd_demo.domain.weighting import WeightScheme, counts


@dataclass(frozen=True, slots=True)
class AgreementFactors:
    """All R-factors are in percent; the goodness of fit is dimensionless.

    The ``_bkg`` variants are background-corrected: their denominators use
    Yobs - Bkg, so a high background can no longer flatter the fit.
    """

    r_wp: float
    r_exp: float
    gof: float
    r_p: float
    r_wp_bkg: float
    r_exp_bkg: float
    r_p_bkg: float


def agreement_factors(
    pattern: Pattern, scheme: WeightScheme, degrees_of_freedom: int
) -> AgreementFactors:
    """Compute the factors over the whole pattern.

    ``degrees_of_freedom`` is N - P + C: points, minus refined parameters, plus
    constraints among them.
    """
    if degrees_of_freedom <= 0:
        raise InsufficientDataError(
            f"N - P + C = {degrees_of_freedom}: the pattern has no more points "
            "than the refinement has free parameters."
        )

    weighted_misfit = []  # w * (Yobs - Ycalc)^2
    weighted_signal = []  # w * Yobs^2
    weighted_net = []  # w * (Yobs - Bkg)^2
    misfit, signal, net = [], [], []
    for y_obs, y_calc, bkg in zip(pattern.y_obs, pattern.y_calc, pattern.background, strict=True):
        y = counts(y_obs)
        w = scheme.weight(y_obs)
        d = y_obs - y_calc
        weighted_misfit.append(w * d * d)
        weighted_signal.append(w * y * y)
        weighted_net.append(w * (y - bkg) ** 2)
        misfit.append(abs(d))
        signal.append(abs(y))
        net.append(abs(y - bkg))

    chi = math.fsum(weighted_misfit)
    total, total_net = math.fsum(weighted_signal), math.fsum(weighted_net)
    profile, profile_net = math.fsum(signal), math.fsum(net)
    if total_net == 0.0 or profile_net == 0.0:
        raise InsufficientDataError(
            "The background equals Yobs at every point, so the "
            "background-corrected factors are undefined."
        )

    return AgreementFactors(
        r_wp=100.0 * math.sqrt(chi / total),
        r_exp=100.0 * math.sqrt(degrees_of_freedom / total),
        gof=math.sqrt(chi / degrees_of_freedom),
        r_p=100.0 * math.fsum(misfit) / profile,
        r_wp_bkg=100.0 * math.sqrt(chi / total_net),
        r_exp_bkg=100.0 * math.sqrt(degrees_of_freedom / total_net),
        r_p_bkg=100.0 * math.fsum(misfit) / profile_net,
    )
