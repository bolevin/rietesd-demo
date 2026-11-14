# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: one-file Windows executable.
#     pyinstaller packaging/rietesd-demo.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent
PACKAGE = ROOT / "src" / "rietesd_demo"

datas = [(str(PACKAGE / "data"), "rietesd_demo/data")]
binaries = []
hiddenimports = []
for library in ("qfluentwidgets", "qframelesswindow", "pyqtgraph"):
    found = collect_all(library)
    datas += found[0]
    binaries += found[1]
    hiddenimports += found[2]

a = Analysis(
    [str(PACKAGE / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQuick3D",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.QtDataVisualization",
        "PySide6.QtCharts",
        "PySide6.QtDesigner",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtBluetooth",
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="rietesd-demo",
    console=False,
    upx=True,
    icon=str(PACKAGE / "data" / "icon.ico"),
)
