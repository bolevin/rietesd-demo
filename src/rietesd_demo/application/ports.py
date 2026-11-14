"""Ports: what the use cases need from the outside world.

The application owns these interfaces; adapters implement them.  Supporting
another input format or another report layout means writing one new adapter -
no use case and no line of the calculation changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from rietesd_demo.domain import Pattern

if TYPE_CHECKING:
    from rietesd_demo.application.service import AnalysisRun


class PatternFormatError(Exception):
    """The file was read, but it is not a pattern in the expected format."""


class PatternReader(Protocol):
    def read(self, path: Path) -> Pattern:
        """Parse ``path``.  Raises OSError, PatternFormatError or InvalidPatternError."""
        ...


class ReportRenderer(Protocol):
    def render(self, run: AnalysisRun) -> str:
        """The finished analysis as a document."""
        ...


class TextStore(Protocol):
    def save(self, path: Path, text: str) -> None:
        """Persist ``text``.  Raises OSError."""
        ...
