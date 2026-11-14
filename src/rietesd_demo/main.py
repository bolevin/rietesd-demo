"""Composition root: the only place that knows every concrete class."""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from rietesd_demo import __version__
from rietesd_demo.adapters.files import FileTextStore
from rietesd_demo.adapters.text_report import PlainTextReport
from rietesd_demo.adapters.topas import TopasReader
from rietesd_demo.application import AnalysisService


def data_path(name: str) -> Path:
    """A file shipped inside the package (also inside the frozen .exe)."""
    return Path(str(resources.files("rietesd_demo") / "data" / name))


def build_service() -> AnalysisService:
    return AnalysisService(reader=TopasReader(), renderer=PlainTextReport(), store=FileTextStore())


def _selftest() -> int:
    """Load the bundled sample, analyse it and check the result is sane."""
    from rietesd_demo.domain import AnalysisSettings

    service = build_service()
    run = service.analyse(
        service.load(data_path("sample_pattern.txt")),
        AnalysisSettings(n_parameters=27, n_constraints=2),
    )
    ok = run.result.n_points == 5501 and abs(run.result.esd_coefficient - 2.283028) < 1e-5
    print(f"SELFTEST {'OK' if ok else 'FAIL'}  coefficient = {run.result.esd_coefficient:.6f}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rietesd-demo", description=__doc__)
    parser.add_argument("pattern", nargs="?", type=Path, help="pattern file to open")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--selftest", action="store_true", help="verify the build and exit")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()

    # Qt is imported here so that --selftest and --version need no display
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication
    from qfluentwidgets import Theme, setTheme, setThemeColor

    from rietesd_demo.ui.main_window import MainWindow
    from rietesd_demo.ui.presenter import MainPresenter

    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Segoe UI", 10))
    setTheme(Theme.AUTO)
    setThemeColor("#0067c0")

    window = MainWindow(QIcon(str(data_path("icon.ico"))))
    presenter = MainPresenter(window, build_service(), data_path("sample_pattern.txt"))
    window.bind(presenter)
    window.show()
    if args.pattern is not None:
        presenter.load(args.pattern)
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
