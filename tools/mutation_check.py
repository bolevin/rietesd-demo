"""Test the tests: break the code on purpose and expect the suite to notice.

    python tools/mutation_check.py

Each mutation below is one plausible mistake.  It is applied to a temporary copy
of the project, the named tests are run against the copy, and they must FAIL.
A mutation that survives means a guard that guards nothing - the script then
exits with status 1.  The working tree is never touched.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Mutation:
    name: str
    file: str
    old: str
    new: str
    tests: str


MUTATIONS = [
    Mutation(
        "Berar: sigma of the current point instead of the previous one",
        "src/rietesd_demo/domain/berar.py",
        "current = residual**2 / previous_sigma**2",
        "current = residual**2 / sigma**2",
        "tests/domain/test_golden.py",
    ),
    Mutation(
        "Berar: a run is never closed",
        "src/rietesd_demo/domain/berar.py",
        "            in_run = False\n\n        previous",
        "            in_run = True\n\n        previous",
        "tests/domain",
    ),
    Mutation(
        "Berar: linking probability not normalised",
        "src/rietesd_demo/domain/berar.py",
        "p = p / (2.0 + p)",
        "p = p / (1.0 + p)",
        "tests/domain/test_berar.py",
    ),
    Mutation(
        "Durbin-Watson: quantile rounded",
        "src/rietesd_demo/domain/statistics.py",
        "NORMAL_QUANTILE_0_1_PERCENT = 3.0902",
        "NORMAL_QUANTILE_0_1_PERCENT = 3.09",
        "tests/domain/test_statistics.py",
    ),
    Mutation(
        "Durbin-Watson: d equal to Q counted as correlated",
        "src/rietesd_demo/domain/statistics.py",
        "if d < q:",
        "if d <= q:",
        "tests/domain/test_statistics.py",
    ),
    Mutation(
        "Agreement: Rexp takes the background-corrected denominator",
        "src/rietesd_demo/domain/agreement.py",
        "r_exp=100.0 * math.sqrt(degrees_of_freedom / total),",
        "r_exp=100.0 * math.sqrt(degrees_of_freedom / total_net),",
        "tests/domain/test_agreement.py",
    ),
    Mutation(
        "Agreement: background ignored in the corrected factors",
        "src/rietesd_demo/domain/agreement.py",
        "weighted_net.append(w * (y - bkg) ** 2)",
        "weighted_net.append(w * y**2)",
        "tests/domain/test_agreement.py",
    ),
    Mutation(
        "Weights: the second scheme silently equals the first",
        "src/rietesd_demo/domain/weighting.py",
        "return 1.0 / math.sqrt(y)",
        "return 1.0 / y",
        "tests/domain/test_statistics.py",
    ),
    Mutation(
        "Pattern: window drops its upper end",
        "src/rietesd_demo/domain/pattern.py",
        "if lo <= t <= hi]",
        "if lo <= t < hi]",
        "tests/domain/test_pattern.py",
    ),
    Mutation(
        "Pattern: negative intensities accepted",
        "src/rietesd_demo/domain/pattern.py",
        "if any(y < 0.0 for y in self.y_obs):",
        "if False:",
        "tests/domain/test_pattern.py",
    ),
    Mutation(
        "Reader: Ycalc derived with the wrong sign",
        "src/rietesd_demo/adapters/topas.py",
        "tuple(o - d for o, d in",
        "tuple(o + d for o, d in",
        "tests/adapters/test_topas.py",
    ),
    Mutation(
        "Reader: NaN accepted as data",
        "src/rietesd_demo/adapters/topas.py",
        "return values if all(math.isfinite(v) for v in values) else None",
        "return values",
        "tests/adapters/test_topas.py",
    ),
    Mutation(
        "Presenter: a failed calculation leaves the old result on screen",
        "src/rietesd_demo/ui/presenter.py",
        "            self._run = None\n            self._view.clear_result()\n",
        "            self._run = None\n",
        "tests/ui/test_presenter.py",
    ),
    Mutation(
        "Presenter: the 2Theta window is ignored",
        "src/rietesd_demo/ui/presenter.py",
        "two_theta_min=None if raw.two_theta_min <= low else raw.two_theta_min,",
        "two_theta_min=None,",
        "tests/ui/test_presenter.py",
    ),
    Mutation(
        "Window: number fields follow the system locale",
        "src/rietesd_demo/ui/main_window.py",
        "            spin.setLocale(number_locale)\n",
        "",
        "tests/ui/test_main_window.py",
    ),
    Mutation(
        "Window: plot keeps its colours on a theme switch",
        "src/rietesd_demo/ui/main_window.py",
        "        self.page.plot.set_dark(dark)\n        self.page.verdict.update()",
        "        self.page.verdict.update()",
        "tests/ui/test_main_window.py",
    ),
    Mutation(
        "Architecture: the calculation starts to depend on numpy",
        "src/rietesd_demo/domain/pattern.py",
        "import math\n",
        "import math\n\nimport numpy\n",
        "tests/architecture",
    ),
    Mutation(
        "Architecture: the presenter reaches for Qt",
        "src/rietesd_demo/ui/presenter.py",
        "import math\n",
        "import math\n\nfrom PySide6.QtCore import Qt\n",
        "tests/architecture",
    ),
]


def run(mutation: Mutation, work: Path) -> bool:
    """True if the tests failed, i.e. the mutation was caught."""
    target = work / mutation.file
    source = (ROOT / mutation.file).read_text("utf-8")
    if source.count(mutation.old) != 1:
        sys.exit(f"{mutation.name}: the text to replace occurs {source.count(mutation.old)} times")
    target.write_text(source.replace(mutation.old, mutation.new), "utf-8", newline="\n")
    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", mutation.tests],
            cwd=work,
            env={
                **os.environ,
                "PYTHONPATH": str(work / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        target.write_text(source, "utf-8", newline="\n")
    return done.returncode == 1  # 1 = tests ran and failed; anything else is not a catch


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in ("src", "tests"):
            shutil.copytree(ROOT / name, work / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "pyproject.toml", work)
        shutil.copy(ROOT / "README.md", work)

        control = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=work,
            env={**os.environ, "PYTHONPATH": str(work / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        if control.returncode != 0:
            sys.exit("Control run failed: the unmutated copy must pass.\n" + control.stdout)
        print("control: unmutated copy passes")

        survived = []
        for mutation in MUTATIONS:
            caught = run(mutation, work)
            print(f"  {'caught  ' if caught else 'SURVIVED'}  {mutation.name}")
            if not caught:
                survived.append(mutation.name)

    print(f"\n{len(MUTATIONS) - len(survived)} of {len(MUTATIONS)} mutations caught")
    sys.exit(1 if survived else 0)


if __name__ == "__main__":
    main()
