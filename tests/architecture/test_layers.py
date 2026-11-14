"""The dependency rule of the architecture, held by a test.

The contracts live in ``pyproject.toml`` under ``[tool.importlinter]``:
dependencies point inwards, the calculation uses the standard library only,
and the presenter never touches Qt.  See docs/architecture.md, section 5.4.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_import_contracts_hold() -> None:
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from importlinter.cli import lint_imports; sys.exit(lint_imports())",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "Contracts: 3 kept, 0 broken" in done.stdout


def test_domain_imports_nothing_but_the_standard_library() -> None:
    """A second, independent look: read the import statements themselves."""
    import ast

    allowed = set(sys.stdlib_module_names) | {"rietesd_demo"}
    for path in (ROOT / "src" / "rietesd_demo" / "domain").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            assert set(roots) <= allowed, f"{path.name} imports {roots}"
