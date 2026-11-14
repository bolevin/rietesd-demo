"""The Qt window: a passive view.  It shows what it is given and reports clicks."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Protocol

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    DoubleSpinBox,
    FluentWindow,
    IconWidget,
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    NavigationItemPosition,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    SegmentedWidget,
    SpinBox,
    StrongBodyLabel,
    Theme,
    isDarkTheme,
    setFont,
    setTheme,
)
from qfluentwidgets import FluentIcon as Icon

from rietesd_demo import __version__
from rietesd_demo.domain import WeightScheme
from rietesd_demo.ui.plot import PlotPanel
from rietesd_demo.ui.presenter import WINDOW_DECIMALS
from rietesd_demo.ui.view import (
    Metric,
    PatternViewModel,
    ResultViewModel,
    SettingsInput,
    Tone,
)

_MUTED = ("#6b6b6b", "#a6a6a6")  # light theme, dark theme
_ACCENT = ("#0067c0", "#4cc2ff")
_EMPTY = "—"

ABOUT = f"""\
RietESD Demo {__version__}

Least squares assumes that the residuals of neighbouring points are independent.
In a Rietveld refinement they rarely are, and the estimated standard deviations
(e.s.d.'s) of the refined parameters come out too small.

This program reads a refined powder pattern and reports
  - the Durbin-Watson statistic d and its critical value Q (Hill & Flack, 1987);
  - the coefficient by which the e.s.d.'s have to be multiplied
    (Berar & Lelann, 1991);
  - the agreement factors Rwp, Rexp, Rp and GoF, as refined and
    background-corrected.

It is a demonstration version of RietESD by Aleksandr A. Levin and Boris A. Levin
(method and original program: A. A. Levin, DOI 10.13140/RG.2.2.27758.69444).
The full program adds batch processing, Bragg factors, angular corrections,
intensity modeling and further families of agreement factors.

Free software under the GNU General Public License, version 3 or later.
"""


class Actions(Protocol):
    """The intents the window forwards; implemented by the presenter."""

    def open_file(self) -> None: ...

    def open_sample(self) -> None: ...

    def calculate(self) -> None: ...

    def save_report(self) -> None: ...


class MetricCard(CardWidget):
    """Caption, a large value, and a line of context underneath."""

    def __init__(self, caption: str, *, headline: bool = False) -> None:
        super().__init__()
        self.setMinimumHeight(104)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        self.caption = CaptionLabel(caption)
        self.caption.setTextColor(*_MUTED)
        self.value = BodyLabel(_EMPTY)
        setFont(self.value, 30 if headline else 22, QFont.Weight.DemiBold)
        if headline:
            self.value.setTextColor(*_ACCENT)
        self.hint = CaptionLabel("")
        self.hint.setTextColor(*_MUTED)
        layout.addWidget(self.caption)
        layout.addStretch(1)
        layout.addWidget(self.value)
        layout.addWidget(self.hint)

    def show_metric(self, metric: Metric | None) -> None:
        self.value.setText(metric.value if metric else _EMPTY)
        self.hint.setText(metric.hint if metric else "")


class VerdictBar(QFrame):
    """The conclusion of the Durbin-Watson test, coloured by its tone."""

    _FILL: ClassVar[dict[Tone, tuple[str, str]]] = {  # light theme, dark theme
        Tone.WARNING: ("#fff4ce", "#433519"),
        Tone.GOOD: ("#dff6dd", "#393d1b"),
    }
    _ICON: ClassVar[dict[Tone, InfoBarIcon]] = {
        Tone.WARNING: InfoBarIcon.WARNING,
        Tone.GOOD: InfoBarIcon.SUCCESS,
    }

    def __init__(self) -> None:
        super().__init__()
        self._tone = Tone.GOOD
        self.icon = IconWidget()
        self.icon.setFixedSize(18, 18)
        self.title = StrongBodyLabel("")
        self.text = BodyLabel("")
        self.text.setWordWrap(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        layout.addWidget(self.icon)
        layout.addWidget(self.title)
        layout.addWidget(self.text, 1)
        self.hide()

    def show_verdict(self, title: str, text: str, tone: Tone) -> None:
        self._tone = tone
        self.icon.setIcon(self._ICON[tone])
        self.title.setText(title)
        self.text.setText(text)
        self.show()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        light, dark = self._FILL[self._tone]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(dark if isDarkTheme() else light))
        painter.drawRoundedRect(self.rect(), 6, 6)


def _titled_card(title: str) -> tuple[CardWidget, QVBoxLayout]:
    card = CardWidget()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 16)
    layout.setSpacing(10)
    layout.addWidget(StrongBodyLabel(title))
    return card, layout


class AnalysisPage(QWidget):
    METRICS = ("Durbin-Watson d", "Rwp, %", "Rexp, %", "Rp, %", "GoF")

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("analysisPage")
        number_locale = QLocale.c()  # "." as decimal separator, everywhere

        # ---- left column: input -------------------------------------
        pattern_card, pattern_box = _titled_card("Pattern")
        self.file_label = BodyLabel("No file loaded")
        self.title_label = CaptionLabel("")
        self.title_label.setWordWrap(True)
        self.title_label.setTextColor(*_MUTED)
        self.summary_label = CaptionLabel("")
        self.summary_label.setTextColor(*_MUTED)
        self.open_button = PushButton(Icon.FOLDER, "Open file")
        self.sample_button = PushButton(Icon.DOCUMENT, "Load sample")
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.sample_button)
        for widget in (self.file_label, self.title_label, self.summary_label):
            pattern_box.addWidget(widget)
        pattern_box.addLayout(buttons)

        settings_card, settings_box = _titled_card("Refinement")
        self.parameters_spin = SpinBox()
        self.constraints_spin = SpinBox()
        for spin in (self.parameters_spin, self.constraints_spin):
            spin.setRange(0, 9999)
        self.weights_combo = ComboBox()
        for scheme in WeightScheme:
            self.weights_combo.addItem(f"w = {scheme.value}", userData=scheme)
        self.low_spin = DoubleSpinBox()
        self.high_spin = DoubleSpinBox()
        for spin in (self.low_spin, self.high_spin):
            spin.setDecimals(WINDOW_DECIMALS)
            spin.setSingleStep(1.0)
            spin.setRange(0.0, 180.0)
            spin.setLocale(number_locale)
        self.high_spin.setValue(180.0)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        rows = (
            ("Refined parameters, P", self.parameters_spin),
            ("Constraints, C", self.constraints_spin),
            ("Weights", self.weights_combo),
            ("2Theta from, deg", self.low_spin),
            ("2Theta to, deg", self.high_spin),
        )
        for row, (caption, widget) in enumerate(rows):
            grid.addWidget(BodyLabel(caption), row, 0)
            grid.addWidget(widget, row, 1)
        grid.setColumnStretch(0, 1)
        settings_box.addLayout(grid)

        self.calculate_button = PrimaryPushButton(Icon.PLAY, "Calculate")
        self.save_button = PushButton(Icon.SAVE, "Save report")
        self.calculate_button.setEnabled(False)
        self.save_button.setEnabled(False)

        left = QVBoxLayout()
        left.setSpacing(12)
        left.addWidget(pattern_card)
        left.addWidget(settings_card)
        left.addWidget(self.calculate_button)
        left.addWidget(self.save_button)
        left.addStretch(1)
        left_holder = QWidget()
        left_holder.setLayout(left)
        left_holder.setFixedWidth(344)
        left.setContentsMargins(0, 0, 0, 0)

        # ---- right column: results ----------------------------------
        self.headline_card = MetricCard("e.s.d. coefficient", headline=True)
        self.metric_cards = [MetricCard(caption) for caption in self.METRICS]
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(self.headline_card, 4)
        for card in self.metric_cards:
            # the Durbin-Watson card has the longest caption
            metrics.addWidget(card, 4 if card is self.metric_cards[0] else 3)

        self.verdict = VerdictBar()

        self.tabs = SegmentedWidget()
        self.plot = PlotPanel()
        self.report = PlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setFont(QFont("Consolas", 10))
        self.report.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        self.report.setPlaceholderText("The report appears here after the calculation.")
        plot_card = CardWidget()
        plot_layout = QVBoxLayout(plot_card)
        plot_layout.setContentsMargins(6, 6, 6, 6)
        plot_layout.addWidget(self.plot)
        self.stack = QStackedWidget()
        self.stack.addWidget(plot_card)
        self.stack.addWidget(self.report)
        self.tabs.addItem("plot", "Pattern", lambda: self.stack.setCurrentIndex(0))
        self.tabs.addItem("report", "Report", lambda: self.stack.setCurrentIndex(1))
        self.tabs.setCurrentItem("plot")
        tabs_row = QHBoxLayout()
        tabs_row.addWidget(self.tabs)
        tabs_row.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(12)
        right.addLayout(metrics)
        right.addWidget(self.verdict)
        right.addLayout(tabs_row)
        right.addWidget(self.stack, 1)

        page = QHBoxLayout(self)
        page.setContentsMargins(24, 16, 24, 24)
        page.setSpacing(20)
        page.addWidget(left_holder)
        page.addLayout(right, 1)


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("aboutPage")
        card, box = _titled_card("About")
        text = BodyLabel(ABOUT)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(text)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.addWidget(card)
        layout.addStretch(1)


class MainWindow(FluentWindow):
    """Implements :class:`rietesd_demo.ui.view.MainView`."""

    def __init__(self, icon: QIcon | None = None) -> None:
        super().__init__()
        self.setWindowTitle("RietESD Demo")
        if icon is not None:
            self.setWindowIcon(icon)
        self.resize(1280, 800)
        self.setMinimumSize(1160, 720)

        self.page = AnalysisPage()
        self.about = AboutPage()
        self.addSubInterface(self.page, Icon.HOME, "Analysis")
        self.addSubInterface(self.about, Icon.INFO, "About", NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=Icon.CONSTRACT,
            text="Light / dark",
            onClick=self.toggle_theme,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.page.plot.set_dark(isDarkTheme())

    def bind(self, actions: Actions) -> None:
        self._actions = actions  # the connections below do not keep it alive
        self.page.open_button.clicked.connect(actions.open_file)
        self.page.sample_button.clicked.connect(actions.open_sample)
        self.page.calculate_button.clicked.connect(actions.calculate)
        self.page.save_button.clicked.connect(actions.save_report)

    def toggle_theme(self) -> None:
        self.set_dark(not isDarkTheme())

    def set_dark(self, dark: bool) -> None:
        setTheme(Theme.DARK if dark else Theme.LIGHT)
        self.page.plot.set_dark(dark)
        self.page.verdict.update()

    # ---- MainView ------------------------------------------------------
    def show_pattern(self, pattern: PatternViewModel) -> None:
        page = self.page
        page.file_label.setText(pattern.file_name)
        page.title_label.setText(pattern.title)
        page.title_label.setVisible(bool(pattern.title))
        page.summary_label.setText(pattern.summary)
        for spin in (page.low_spin, page.high_spin):
            spin.setRange(pattern.window_low, pattern.window_high)
        page.low_spin.setValue(pattern.window_low)
        page.high_spin.setValue(pattern.window_high)
        page.plot.set_pattern(pattern)
        page.calculate_button.setEnabled(True)

    def show_result(self, result: ResultViewModel) -> None:
        page = self.page
        page.headline_card.show_metric(result.headline)
        for card, metric in zip(page.metric_cards, result.metrics, strict=True):
            card.show_metric(metric)
        page.verdict.show_verdict(result.verdict_title, result.verdict_text, result.tone)
        page.report.setPlainText(result.report)
        page.save_button.setEnabled(True)

    def clear_result(self) -> None:
        page = self.page
        page.headline_card.show_metric(None)
        for card in page.metric_cards:
            card.show_metric(None)
        page.verdict.hide()
        page.report.clear()
        page.save_button.setEnabled(False)

    def show_error(self, title: str, message: str) -> None:
        InfoBar.error(
            title, message, duration=8000, position=InfoBarPosition.TOP_RIGHT, parent=self
        )

    def show_success(self, title: str, message: str) -> None:
        InfoBar.success(
            title, message, duration=5000, position=InfoBarPosition.TOP_RIGHT, parent=self
        )

    def settings(self) -> SettingsInput:
        page = self.page
        return SettingsInput(
            n_parameters=page.parameters_spin.value(),
            n_constraints=page.constraints_spin.value(),
            weighting=page.weights_combo.currentData(),
            two_theta_min=page.low_spin.value(),
            two_theta_max=page.high_spin.value(),
        )

    def ask_open_path(self) -> Path | None:
        name, _ = QFileDialog.getOpenFileName(
            self, "Open pattern", "", "TOPAS pattern (*.txt *.xy *.csv);;All files (*)"
        )
        return Path(name) if name else None

    def ask_save_path(self, suggested: Path) -> Path | None:
        name, _ = QFileDialog.getSaveFileName(
            self, "Save report", str(suggested), "Text file (*.txt);;All files (*)"
        )
        return Path(name) if name else None
