# Third-party notices

RietESD Demo is licensed under the GNU General Public License, version 3 or later
(see `LICENSE`). It uses the components below. Versions are those the project was
developed and tested with; `pyproject.toml` states the accepted ranges.

| Component | Version | Licence | Notes |
|---|---|---|---|
| [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt for Python) | 6.11.1 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | used under the LGPL-3.0 option |
| shiboken6 | 6.11.1 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | binding runtime for PySide6 |
| [PySide6-Fluent-Widgets](https://qfluentwidgets.com) (`qfluentwidgets`) | 1.11.2 | **GPL-3.0** | the widget set the window is built from |
| [PySideSix-Frameless-Window](https://pypi.org/project/PySideSix-Frameless-Window/) (`qframelesswindow`) | 0.8.1 | LGPL-3.0 | pulled in by PySide6-Fluent-Widgets |
| [pyqtgraph](https://www.pyqtgraph.org) | 0.14.0 | MIT | the plot |
| [darkdetect](https://github.com/albertosottile/darkdetect) | 0.8.0 | BSD-3-Clause | pulled in by PySide6-Fluent-Widgets |
| [NumPy](https://numpy.org) | 2.4.6 | BSD-3-Clause | used by the plot only |
| [PyInstaller](https://pyinstaller.org) | 6.x | GPL-2.0-or-later with the bootloader exception | build tool for the executable |

Development tools (pytest, pytest-qt, hypothesis, ruff, mypy, import-linter, Pillow) are
not part of the program and are not distributed with it.

## Why the program is GPL-3.0-or-later

`qfluentwidgets` is offered under GPL-3.0 (a commercial licence is sold separately). The
window is built on it, so the program as a whole is covered by the GPL, and the GPL does
not allow further restrictions to be added. Anyone may use, study, modify and redistribute
RietESD Demo; every derivative must stay under the same terms.

The calculation (`rietesd_demo.domain`), the use cases (`rietesd_demo.application`) and the
presenter import nothing beyond the Python standard library. This is checked on every
test run.

## Distributing the executable

`rietesd-demo.exe` embeds all of the above. Whoever passes the executable on must make the
corresponding source available, which is what this repository is for.

## Sources of the dependencies

Every component is on PyPI and installs with `pip install -e .`. Their licence texts ship
inside the installed packages, under `<site-packages>/<package>-<version>.dist-info/`.
