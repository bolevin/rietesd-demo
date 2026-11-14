"""The real window, driven through its widgets."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QLocale, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot
from qfluentwidgets import Theme, isDarkTheme, setTheme

from rietesd_demo.main import build_service
from rietesd_demo.ui.main_window import MainWindow
from rietesd_demo.ui.plot import DARK, LIGHT
from rietesd_demo.ui.presenter import MainPresenter


@pytest.fixture
def window(qtbot: QtBot, sample_path: Path) -> MainWindow:
    setTheme(Theme.LIGHT)
    window = MainWindow()
    qtbot.addWidget(window)
    window.bind(MainPresenter(window, build_service(), sample_path))
    return window


def click(button: QWidget) -> None:
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)


def test_nothing_can_be_calculated_before_a_pattern_is_loaded(window: MainWindow) -> None:
    assert not window.page.calculate_button.isEnabled()
    assert not window.page.save_button.isEnabled()
    assert window.page.verdict.isHidden()


def test_load_calculate_and_read_the_result(qtbot: QtBot, window: MainWindow) -> None:
    page = window.page
    click(page.sample_button)
    assert page.file_label.text() == "sample_pattern.txt"
    assert page.calculate_button.isEnabled()
    assert (page.low_spin.value(), page.high_spin.value()) == (10.0, 120.0)

    page.parameters_spin.setValue(27)
    page.constraints_spin.setValue(2)
    click(page.calculate_button)

    assert page.headline_card.value.text() == "2.283"
    assert [card.value.text() for card in page.metric_cards] == [
        "1.019",
        "3.60",
        "2.50",
        "2.56",
        "1.439",
    ]
    assert not page.verdict.isHidden()
    assert page.verdict.title.text() == "Positive serial correlation"
    assert "Coefficient .......... 2.2830" in page.report.toPlainText()
    assert page.save_button.isEnabled()


def test_weights_combo_selects_the_scheme(qtbot: QtBot, window: MainWindow) -> None:
    page = window.page
    click(page.sample_button)
    page.parameters_spin.setValue(27)
    page.constraints_spin.setValue(2)
    page.weights_combo.setCurrentIndex(1)
    click(page.calculate_button)
    assert page.headline_card.value.text() == "2.656"


def test_an_error_clears_the_result_and_disables_saving(qtbot: QtBot, window: MainWindow) -> None:
    page = window.page
    click(page.sample_button)
    click(page.calculate_button)
    assert page.save_button.isEnabled()
    page.constraints_spin.setValue(5)  # C > P = 0
    click(page.calculate_button)
    assert page.headline_card.value.text() == "—"
    assert page.verdict.isHidden()
    assert not page.save_button.isEnabled()


def test_numbers_use_a_point_whatever_the_system_locale(qtbot: QtBot, sample_path: Path) -> None:
    QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
    try:
        window = MainWindow()
        qtbot.addWidget(window)
        window.bind(MainPresenter(window, build_service(), sample_path))
        click(window.page.sample_button)
        assert window.page.low_spin.text() == "10.000"
        assert window.page.high_spin.text() == "120.000"
    finally:
        QLocale.setDefault(QLocale.c())


def test_theme_switch_recolours_the_plot(qtbot: QtBot, window: MainWindow) -> None:
    click(window.page.sample_button)
    plot = window.page.plot
    assert plot._palette is LIGHT
    window.toggle_theme()
    assert isDarkTheme()
    assert plot._palette is DARK
    background = plot._graphics.backgroundBrush().color().name()
    assert background == DARK.background
    window.toggle_theme()
    assert plot._palette is LIGHT


def test_tabs_switch_between_plot_and_report(window: MainWindow) -> None:
    page = window.page
    assert page.stack.currentIndex() == 0
    page.tabs.setCurrentItem("report")
    page.tabs.items["report"].click()
    assert page.stack.currentIndex() == 1
