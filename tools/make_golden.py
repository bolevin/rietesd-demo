"""Record the reference values the golden-master test compares against.

    set RIETESD_FULL_APP=C:\\path\\to\\rietesd-app
    python tools/make_golden.py

The values come from the full RietESD program (not part of this repository),
run on the bundled synthetic pattern.  The demo was written independently of
that code base; agreeing with it to seven digits is the evidence that the
calculation is right.  The JSON this script writes is committed, so the test
itself needs nothing but the repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "src" / "rietesd_demo" / "data" / "sample_pattern.txt"
OUT = ROOT / "tests" / "golden" / "sample_reference.json"
P, C = 27, 2
FIELDS = {  # name in the JSON -> attribute of the full program's result
    "n_points": "n",
    "durbin_watson": "dw_calc",
    "critical_value": "q",
    "esd_coefficient": "coeff",
    "r_wp": "rwp",
    "r_exp": "rexp",
    "gof": "gof",
    "r_p": "rp",
    "r_wp_bkg": "crwp",
    "r_exp_bkg": "crexp",
    "r_p_bkg": "crp",
}


def main() -> None:
    full_app = os.environ.get("RIETESD_FULL_APP")
    if not full_app or not (Path(full_app) / "rietesd_core.py").exists():
        sys.exit("Set RIETESD_FULL_APP to the folder of the full RietESD program.")
    sys.path.insert(0, full_app)
    from rietesd_core import Inputs, compute, parse_input  # type: ignore[import-not-found]
    from rietesd_report import APP_VERSION  # type: ignore[import-not-found]

    pattern = parse_input(str(SAMPLE))
    cases = {}
    for label, iweight in (("1/Yobs", 1), ("1/sqrt(Yobs)", 2)):
        result = compute(pattern, Inputs(npar=P, nc=C, iweight=iweight, peaks_to_bkg=[]))
        cases[label] = {name: getattr(result, attr) for name, attr in FIELDS.items()}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "reference": f"RietESD {APP_VERSION} (full program)",
                "note": "The full program rounds its factors to single precision, "
                "so the values carry about seven significant digits.",
                "pattern_sha256": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
                "n_parameters": P,
                "n_constraints": C,
                "cases": cases,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
