"""The whole calculation as one pure function: pattern + settings -> result."""

from __future__ import annotations

from dataclasses import dataclass

from rietesd_demo.domain.agreement import AgreementFactors, agreement_factors
from rietesd_demo.domain.berar import esd_coefficient
from rietesd_demo.domain.errors import InsufficientDataError
from rietesd_demo.domain.pattern import Pattern
from rietesd_demo.domain.statistics import (
    Correlation,
    classify,
    critical_value,
    durbin_watson,
)
from rietesd_demo.domain.weighting import WeightScheme

#: Below this the statistics are arithmetic, not evidence.
MIN_POINTS = 3


@dataclass(frozen=True, slots=True)
class AnalysisSettings:
    """What the user knows about the refinement that produced the pattern."""

    n_parameters: int = 0  # P - all refined parameters
    n_constraints: int = 0  # C - constraints among them
    weighting: WeightScheme = WeightScheme.INVERSE_INTENSITY
    two_theta_min: float | None = None
    two_theta_max: float | None = None

    def __post_init__(self) -> None:
        if self.n_parameters < 0 or self.n_constraints < 0:
            raise ValueError("P and C must not be negative.")
        if self.n_constraints > self.n_parameters:
            raise ValueError("C cannot exceed P: a constraint ties refined parameters.")
        if (
            self.two_theta_min is not None
            and self.two_theta_max is not None
            and self.two_theta_min > self.two_theta_max
        ):
            raise ValueError("The 2Theta window is empty: minimum exceeds maximum.")


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    n_points: int
    two_theta_range: tuple[float, float]
    durbin_watson: float
    critical_value: float  # Q
    correlation: Correlation
    esd_coefficient: float  # Berar's factor
    factors: AgreementFactors

    @property
    def esd_need_correction(self) -> bool:
        """True when the refinement's e.s.d.'s are too small as printed."""
        return self.correlation is Correlation.POSITIVE


def analyse(pattern: Pattern, settings: AnalysisSettings) -> AnalysisResult:
    """Run every step over the part of the pattern inside the 2Theta window."""
    used = pattern.window(settings.two_theta_min, settings.two_theta_max)
    n = len(used)
    if n < MIN_POINTS:
        raise InsufficientDataError(
            f"Only {n} data point(s) in the 2Theta window; at least {MIN_POINTS} are needed."
        )

    scheme = settings.weighting
    residuals = used.difference
    sigmas = [scheme.sigma(y) for y in used.y_obs]
    weighted = [r / s for r, s in zip(residuals, sigmas, strict=True)]

    d = durbin_watson(weighted)
    q = critical_value(n, settings.n_parameters, settings.n_constraints)
    degrees_of_freedom = n - settings.n_parameters + settings.n_constraints

    return AnalysisResult(
        n_points=n,
        two_theta_range=(used.two_theta[0], used.two_theta[-1]),
        durbin_watson=d,
        critical_value=q,
        correlation=classify(d, q),
        esd_coefficient=esd_coefficient(residuals, sigmas),
        factors=agreement_factors(used, scheme, degrees_of_freedom),
    )
