"""Golden master: the demo against the full RietESD program.

``tests/golden/sample_reference.json`` holds what the full program computes for
the bundled pattern (recorded by ``tools/make_golden.py``).  The two code bases
share no code, so agreement here is independent evidence for both.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from rietesd_demo.domain import AnalysisSettings, Pattern, WeightScheme, analyse

REFERENCE: dict[str, Any] = json.loads(
    (Path(__file__).parents[1] / "golden" / "sample_reference.json").read_text("utf-8")
)
#: the reference values are single precision: seven digits, not sixteen
TOLERANCE = 5e-7


def test_reference_belongs_to_the_bundled_pattern(sample_path: Path) -> None:
    digest = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    assert digest == REFERENCE["pattern_sha256"], (
        "The sample changed; re-record the reference with tools/make_golden.py."
    )


@pytest.mark.parametrize("scheme", list(WeightScheme), ids=lambda s: s.value)
def test_demo_reproduces_the_full_program(sample: Pattern, scheme: WeightScheme) -> None:
    expected = REFERENCE["cases"][scheme.value]
    result = analyse(
        sample,
        AnalysisSettings(REFERENCE["n_parameters"], REFERENCE["n_constraints"], scheme),
    )
    got = {
        "n_points": result.n_points,
        "durbin_watson": result.durbin_watson,
        "critical_value": result.critical_value,
        "esd_coefficient": result.esd_coefficient,
        "r_wp": result.factors.r_wp,
        "r_exp": result.factors.r_exp,
        "gof": result.factors.gof,
        "r_p": result.factors.r_p,
        "r_wp_bkg": result.factors.r_wp_bkg,
        "r_exp_bkg": result.factors.r_exp_bkg,
        "r_p_bkg": result.factors.r_p_bkg,
    }
    assert got.keys() == expected.keys()
    for name, value in expected.items():
        assert got[name] == pytest.approx(value, rel=TOLERANCE), name
