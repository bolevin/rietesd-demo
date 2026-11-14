"""What the presenter may ask of a window, and the data it hands over.

View models carry text that is already formatted and plain tuples of numbers.
The window draws them and decides nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from rietesd_demo.domain import WeightScheme


class Tone(Enum):
    """How a verdict should look: the window maps it to a colour."""

    GOOD = "good"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class PatternViewModel:
    file_name: str
    title: str
    summary: str  # "5501 points, 10.00 - 120.00 deg"
    two_theta: tuple[float, ...]
    y_obs: tuple[float, ...]
    y_calc: tuple[float, ...]
    background: tuple[float, ...]
    difference: tuple[float, ...]
    window_low: float  # limits offered for the 2Theta window
    window_high: float


@dataclass(frozen=True, slots=True)
class Metric:
    caption: str
    value: str
    hint: str = ""


@dataclass(frozen=True, slots=True)
class ResultViewModel:
    headline: Metric  # Berar's coefficient
    metrics: tuple[Metric, ...]
    verdict_title: str
    verdict_text: str
    tone: Tone
    report: str


@dataclass(frozen=True, slots=True)
class SettingsInput:
    """The settings as the widgets hold them."""

    n_parameters: int
    n_constraints: int
    weighting: WeightScheme
    two_theta_min: float
    two_theta_max: float


class MainView(Protocol):
    def show_pattern(self, pattern: PatternViewModel) -> None: ...

    def show_result(self, result: ResultViewModel) -> None: ...

    def clear_result(self) -> None: ...

    def show_error(self, title: str, message: str) -> None: ...

    def show_success(self, title: str, message: str) -> None: ...

    def settings(self) -> SettingsInput: ...

    def ask_open_path(self) -> Path | None: ...

    def ask_save_path(self, suggested: Path) -> Path | None: ...
