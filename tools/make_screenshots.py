"""Render the screenshots used in the README.

    python tools/make_screenshots.py

The window is laid out by the real Windows platform plugin but never appears on
screen; it is rendered at 2x into ``docs/img``.  Every picture shows the bundled
synthetic pattern, so the result is reproducible.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme, setThemeColor

from rietesd_demo.main import build_service, data_path
from rietesd_demo.ui.main_window import MainWindow
from rietesd_demo.ui.presenter import MainPresenter

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"
SCALE = 2
SIZE = (1280, 800)
PAGE = {False: "#f3f3f3", True: "#202020"}  # window background per theme


def settle(app: QApplication, rounds: int = 12) -> None:
    for _ in range(rounds):
        app.processEvents()


def grab(window: MainWindow, dark: bool) -> Image.Image:
    pixmap = QPixmap(window.size() * SCALE)
    pixmap.setDevicePixelRatio(SCALE)
    pixmap.fill(QColor(PAGE[dark]))
    window.render(pixmap, QPoint(0, 0))
    raw = OUT / "_raw.png"
    pixmap.save(str(raw))
    image = Image.open(raw).convert("RGBA")
    image.load()
    raw.unlink()
    return image


def framed(shot: Image.Image, top: str, bottom: str, margin: int = 110) -> Image.Image:
    """The window on a gradient backdrop with rounded corners and a soft shadow."""
    radius = 9 * SCALE
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *shot.size], radius=radius, fill=255)
    width, height = shot.width + 2 * margin, shot.height + 2 * margin

    canvas = Image.new("RGBA", (width, height))
    a, b = (Image.new("RGBA", (1, 1), c).getpixel((0, 0)) for c in (top, bottom))
    draw = ImageDraw.Draw(canvas)
    for y in range(height):
        t = y / (height - 1)
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(round(p + (q - p) * t) for p, q in zip(a, b, strict=True)),
        )

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [margin, margin + 18, margin + shot.width, margin + shot.height + 18],
        radius=radius,
        fill=(0, 0, 0, 120),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
    canvas.paste(shot, (margin, margin), mask)
    return canvas.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setFont(QFont("Segoe UI", 10))
    setTheme(Theme.LIGHT)
    setThemeColor("#0067c0")

    window = MainWindow(QIcon(str(data_path("icon.ico"))))
    window.setMicaEffectEnabled(False)  # Mica is composed by the OS, not by Qt
    presenter = MainPresenter(window, build_service(), data_path("sample_pattern.txt"))
    window.bind(presenter)
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.resize(*SIZE)
    window.show()
    settle(app)

    presenter.open_sample()
    window.page.parameters_spin.setValue(27)
    window.page.constraints_spin.setValue(2)
    presenter.calculate()
    settle(app)

    shots: dict[str, Image.Image] = {}
    for dark in (False, True):
        window.set_dark(dark)
        settle(app)
        shots["dark" if dark else "light"] = grab(window, dark)

    window.set_dark(False)
    window.page.tabs.setCurrentItem("report")
    window.page.stack.setCurrentIndex(1)
    settle(app)
    shots["report"] = grab(window, False)

    window.page.tabs.setCurrentItem("plot")
    window.page.stack.setCurrentIndex(0)
    window.set_dark(True)
    # a single reflection: the run of same-sign residuals is the serial correlation
    window.page.plot._main.setXRange(30.85, 31.75, padding=0)
    window.page.plot._main.setYRange(0, 46000, padding=0)
    window.page.plot._diff.enableAutoRange(axis="y")
    settle(app)
    shots["peak"] = grab(window, True)

    backdrops = {
        "light": ("#cfe3f7", "#8fb8e8"),
        "dark": ("#1b2a41", "#0b1220"),
        "report": ("#cfe3f7", "#8fb8e8"),
        "peak": ("#1b2a41", "#0b1220"),
    }
    for name, shot in shots.items():
        target = OUT / f"demo-{name}.png"
        framed(shot, *backdrops[name]).save(target, optimize=True)
        print(f"wrote {target}  {shot.width}x{shot.height}")
    window.close()


if __name__ == "__main__":
    main()
