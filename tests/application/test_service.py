"""The use cases with every port replaced by a fake: no file is touched."""

from __future__ import annotations

from pathlib import Path

from rietesd_demo.application import AnalysisRun, AnalysisService
from rietesd_demo.domain import AnalysisSettings, Pattern


class FakeReader:
    def __init__(self, pattern: Pattern) -> None:
        self.pattern = pattern
        self.asked: list[Path] = []

    def read(self, path: Path) -> Pattern:
        self.asked.append(path)
        return self.pattern


class FakeRenderer:
    def render(self, run: AnalysisRun) -> str:
        return f"report for {run.source.name}, N = {run.result.n_points}"


class FakeStore:
    def __init__(self) -> None:
        self.saved: dict[Path, str] = {}

    def save(self, path: Path, text: str) -> None:
        self.saved[path] = text


def test_load_analyse_export(tiny: Pattern) -> None:
    reader, store = FakeReader(tiny), FakeStore()
    service = AnalysisService(reader, FakeRenderer(), store)

    loaded = service.load(Path("scan.txt"))
    assert reader.asked == [Path("scan.txt")]
    assert loaded.pattern is tiny

    run = service.analyse(loaded, AnalysisSettings(n_parameters=1))
    assert run.source == Path("scan.txt")
    assert run.settings.n_parameters == 1
    assert run.result.n_points == 4

    assert service.report(run) == "report for scan.txt, N = 4"
    service.export(run, Path("out.txt"))
    assert store.saved == {Path("out.txt"): "report for scan.txt, N = 4"}
