"""The calculation itself: pure functions and immutable values.

Nothing in this package reads a file, opens a window or imports anything
outside the standard library.  The rule is checked in CI (see ``.importlinter``).
"""

from rietesd_demo.domain.agreement import AgreementFactors
from rietesd_demo.domain.analysis import AnalysisResult, AnalysisSettings, analyse
from rietesd_demo.domain.errors import DomainError, InsufficientDataError, InvalidPatternError
from rietesd_demo.domain.pattern import Pattern
from rietesd_demo.domain.statistics import Correlation
from rietesd_demo.domain.weighting import WeightScheme

__all__ = [
    "AgreementFactors",
    "AnalysisResult",
    "AnalysisSettings",
    "Correlation",
    "DomainError",
    "InsufficientDataError",
    "InvalidPatternError",
    "Pattern",
    "WeightScheme",
    "analyse",
]
