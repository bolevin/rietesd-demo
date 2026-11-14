from __future__ import annotations

from pathlib import Path

import pytest

from rietesd_demo.adapters.topas import TopasReader
from rietesd_demo.application import PatternFormatError
from rietesd_demo.domain import InvalidPatternError

GOOD = """\
'A title without commas
'x,Yobs,Ycalc,Diff,Phase 1,Bkg,Peaks Phase:0
10.00,100,90.5,9.5,60,20,25
10.02,400,420,-20,300,21,26
10.04,100,110,-10,70,22,27
"""


def parse(text: str):  # type: ignore[no-untyped-def]
    return TopasReader().parse(text)


def test_columns_are_found_by_name() -> None:
    pattern = parse(GOOD)
    assert pattern.title == "A title without commas"
    assert pattern.two_theta == (10.00, 10.02, 10.04)
    assert pattern.y_obs == (100.0, 400.0, 100.0)
    assert pattern.y_calc == (90.5, 420.0, 110.0)
    assert pattern.background == (20.0, 21.0, 22.0)  # not the phase, not the peak


def test_bundled_sample_reads(sample_path: Path) -> None:
    pattern = TopasReader().read(sample_path)
    assert len(pattern) == 5501
    assert pattern.two_theta[0] == 10.0
    assert pattern.two_theta[-1] == 120.0
    assert pattern.title.startswith("Synthetic demo pattern")


def test_ycalc_is_derived_when_only_diff_is_given() -> None:
    text = "'x,Yobs,Diff,Bkg\n1,100,10,5\n2,200,-20,5\n"
    assert parse(text).y_calc == (90.0, 220.0)


def test_column_names_ignore_case_and_blanks() -> None:
    text = "x , yobs , YCALC , bkg\n1,100,90,5\n2,200,220,5\n"
    assert parse(text).background == (5.0, 5.0)


def test_title_is_optional() -> None:
    assert parse("'x,Yobs,Ycalc,Bkg\n1,100,90,5\n2,200,220,5\n").title == ""


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("just some words\n", "No rows of comma-separated numbers"),
        ("1,100,90,5\n2,200,220,5\n", "column names .* is missing"),
        ("'x,Yobs,Ycalc\n1,100,90\n2,200,220\n", r"background column \(Bkg\) is missing"),
        ("'x,Yobs,Bkg\n1,100,5\n2,200,5\n", "Neither Ycalc nor Diff"),
        ("'x,Yobs,Ycalc,Bkg\n1,100,90,5\n2,200,220\n", "Line 3: 3 values, expected 4"),
        ("'x,Yobs,Ycalc,Bkg\n1,100,90,5\nnote\n2,200,220,5\n", "Line 3: text in the middle"),
        ("'x,Yobs,Ycalc\n1,100,90,5\n2,200,220,5\n", "3 column names but 4 columns"),
    ],
)
def test_malformed_files_are_refused_with_a_reason(text: str, message: str) -> None:
    with pytest.raises(PatternFormatError, match=message):
        parse(text)


def test_not_a_number_never_becomes_data() -> None:
    # float() accepts "nan"; a row holding it must not pass as numbers
    with pytest.raises(PatternFormatError, match="Line 3: text in the middle"):
        parse("'x,Yobs,Ycalc,Bkg\n1,100,90,5\n2,nan,220,5\n")


def test_domain_rules_still_apply() -> None:
    with pytest.raises(InvalidPatternError, match="2Theta must increase"):
        parse("'x,Yobs,Ycalc,Bkg\n2,100,90,5\n1,200,220,5\n")


def test_latin1_files_are_read(tmp_path: Path) -> None:
    path = tmp_path / "old.txt"
    path.write_bytes("'Probe \xb5m\n'x,Yobs,Ycalc,Bkg\n1,100,90,5\n2,200,220,5\n".encode("latin-1"))
    assert TopasReader().read(path).title == "Probe \xb5m"
