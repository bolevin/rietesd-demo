from __future__ import annotations

from pathlib import Path

from rietesd_demo.adapters.files import FileTextStore
from rietesd_demo.adapters.text_report import PlainTextReport
from rietesd_demo.application import AnalysisRun
from rietesd_demo.domain import AnalysisSettings, Pattern, analyse


def run_for(pattern: Pattern, settings: AnalysisSettings) -> AnalysisRun:
    return AnalysisRun(Path("C:/data/scan.txt"), pattern, settings, analyse(pattern, settings))


def test_report_of_the_sample(sample: Pattern) -> None:
    lines = PlainTextReport().render(run_for(sample, AnalysisSettings(27, 2))).splitlines()
    assert "  File ................. scan.txt" in lines
    assert "  Points used, N ....... 5501" in lines
    assert "  Title ................ Synthetic demo pattern (not a measurement):" in lines
    assert "                         cubic perovskite + minor second phase;" in lines
    assert max(map(len, lines)) <= 70
    assert "  2Theta range ......... 10.0000 - 120.0000 deg" in lines
    assert "  Weights .............. w = 1/Yobs" in lines
    assert "  d .................... 1.0189" in lines
    assert "  Q .................... 1.9255" in lines
    assert "  Verdict .............. positive serial correlation (d < Q)" in lines
    assert "  Coefficient .......... 2.2830" in lines
    assert "  Rwp, % ...............        3.598          12.560" in lines
    assert "  GoF ..................        1.439" in lines


def test_advice_follows_the_verdict(tiny: Pattern) -> None:
    # the tiny pattern has d = 2: no correlation, so no instruction to multiply
    text = PlainTextReport().render(run_for(tiny, AnalysisSettings(1)))
    assert "no serial correlation" in text
    assert "can be used as they are" in text
    assert "Multiply them" not in text


def test_store_writes_windows_line_ends(tmp_path: Path) -> None:
    target = tmp_path / "report.txt"
    FileTextStore().save(target, "one\ntwo\n")
    assert target.read_bytes() == b"one\r\ntwo\r\n"
