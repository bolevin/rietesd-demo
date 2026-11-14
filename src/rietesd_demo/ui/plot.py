"""The pattern plot: Yobs, Ycalc and background above, the difference curve below."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedLayout, QWidget
from qfluentwidgets import BodyLabel

from rietesd_demo.ui.view import PatternViewModel

pg.setConfigOptions(antialias=True)


@dataclass(frozen=True, slots=True)
class PlotPalette:
    background: str
    text: str
    axis: str
    observed: str
    calculated: str
    baseline: str
    difference: str
    zero: str


LIGHT = PlotPalette(
    background="#fbfbfb",
    text="#3b3b3b",
    axis="#b4b4b4",
    observed="#1565c0",
    calculated="#d32f2f",
    baseline="#2e7d32",
    difference="#6a1b9a",
    zero="#c8c8c8",
)
DARK = PlotPalette(
    background="#2b2b2b",
    text="#d6d6d6",
    axis="#5a5a5a",
    observed="#5aa9f8",
    calculated="#ff7b72",
    baseline="#7ee787",
    difference="#c9a0ff",
    zero="#555555",
)


class PlotPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pattern: PatternViewModel | None = None
        self._palette = LIGHT

        self._graphics = pg.GraphicsLayoutWidget()
        self._main = self._graphics.addPlot(row=0, col=0)
        self._diff = self._graphics.addPlot(row=1, col=0)
        self._diff.setXLink(self._main)
        grid = self._graphics.ci.layout
        grid.setRowStretchFactor(0, 4)
        grid.setRowStretchFactor(1, 1)
        self._graphics.ci.setContentsMargins(4, 8, 12, 4)
        self._main.getAxis("bottom").setStyle(showValues=False)
        for plot in (self._main, self._diff):
            plot.getAxis("left").setWidth(64)
            plot.setMenuEnabled(False)
            plot.hideButtons()
        self._legend = self._main.addLegend(offset=(-12, 8))

        self._placeholder = BodyLabel("Open a pattern file or load the sample to begin.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._graphics)

        self._apply_palette()

    def set_pattern(self, pattern: PatternViewModel) -> None:
        self._pattern = pattern
        self._draw()
        self._main.enableAutoRange()
        self._diff.enableAutoRange()
        self._stack.setCurrentWidget(self._graphics)

    def set_dark(self, dark: bool) -> None:
        self._palette = DARK if dark else LIGHT
        self._apply_palette()
        self._draw()

    # pyqtgraph resolves colours when an item is created, so a theme change
    # re-applies every pen and rebuilds the curves.
    def _apply_palette(self) -> None:
        p = self._palette
        self._graphics.setBackground(p.background)
        self._legend.setLabelTextColor(p.text)
        for plot in (self._main, self._diff):
            for name in ("left", "bottom"):
                axis = plot.getAxis(name)
                axis.setPen(p.axis)
                axis.setTextPen(p.text)
        self._main.setLabel("left", "Intensity, counts", color=p.text)
        self._diff.setLabel("left", "Yobs - Ycalc", color=p.text)
        self._diff.setLabel("bottom", "2Theta, deg", color=p.text)

    def _draw(self) -> None:
        self._main.clear()
        self._diff.clear()
        if self._pattern is None:
            return
        p, v = self._palette, self._pattern
        x = np.asarray(v.two_theta)
        self._main.plot(
            x,
            np.asarray(v.y_obs),
            pen=None,
            symbol="o",
            symbolSize=3,
            symbolPen=None,
            symbolBrush=p.observed,
            name="Yobs",
        )
        self._main.plot(
            x, np.asarray(v.y_calc), pen=pg.mkPen(p.calculated, width=1.6), name="Ycalc"
        )
        self._main.plot(
            x,
            np.asarray(v.background),
            pen=pg.mkPen(p.baseline, width=1.4, style=Qt.PenStyle.DashLine),
            name="Bkg",
        )
        self._diff.addItem(pg.InfiniteLine(pos=0.0, angle=0, pen=pg.mkPen(p.zero)))
        self._diff.plot(x, np.asarray(v.difference), pen=pg.mkPen(p.difference, width=1.1))
