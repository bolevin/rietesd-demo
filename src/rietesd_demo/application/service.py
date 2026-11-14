"""The three things a user can do: load a pattern, analyse it, export the report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rietesd_demo.application.ports import PatternReader, ReportRenderer, TextStore
from rietesd_demo.domain import AnalysisResult, AnalysisSettings, Pattern, analyse


@dataclass(frozen=True, slots=True)
class LoadedPattern:
    source: Path
    pattern: Pattern


@dataclass(frozen=True, slots=True)
class AnalysisRun:
    """One finished calculation with everything needed to report it."""

    source: Path
    pattern: Pattern
    settings: AnalysisSettings
    result: AnalysisResult


class AnalysisService:
    """Use cases.  Holds no state: every call says what it works on."""

    def __init__(self, reader: PatternReader, renderer: ReportRenderer, store: TextStore) -> None:
        self._reader = reader
        self._renderer = renderer
        self._store = store

    def load(self, path: Path) -> LoadedPattern:
        return LoadedPattern(source=path, pattern=self._reader.read(path))

    def analyse(self, loaded: LoadedPattern, settings: AnalysisSettings) -> AnalysisRun:
        return AnalysisRun(
            source=loaded.source,
            pattern=loaded.pattern,
            settings=settings,
            result=analyse(loaded.pattern, settings),
        )

    def report(self, run: AnalysisRun) -> str:
        return self._renderer.render(run)

    def export(self, run: AnalysisRun, path: Path) -> None:
        self._store.save(path, self._renderer.render(run))
