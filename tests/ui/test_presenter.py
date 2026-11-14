"""The presenter against a fake view: no Qt, no window, no file dialog."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from rietesd_demo.domain import WeightScheme
from rietesd_demo.main import build_service
from rietesd_demo.ui.presenter import MainPresenter
from rietesd_demo.ui.view import PatternViewModel, ResultViewModel, SettingsInput, Tone


@dataclass
class FakeView:
    """Records what it is told to show and answers dialogs from a script."""

    input: SettingsInput = field(
        default_factory=lambda: SettingsInput(27, 2, WeightScheme.INVERSE_INTENSITY, 10.0, 120.0)
    )
    open_path: Path | None = None
    save_path: Path | None = None
    pattern: PatternViewModel | None = None
    result: ResultViewModel | None = None
    errors: list[tuple[str, str]] = field(default_factory=list)
    successes: list[tuple[str, str]] = field(default_factory=list)
    suggested: Path | None = None

    def show_pattern(self, pattern: PatternViewModel) -> None:
        self.pattern = pattern

    def show_result(self, result: ResultViewModel) -> None:
        self.result = result

    def clear_result(self) -> None:
        self.result = None

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def show_success(self, title: str, message: str) -> None:
        self.successes.append((title, message))

    def settings(self) -> SettingsInput:
        return self.input

    def ask_open_path(self) -> Path | None:
        return self.open_path

    def ask_save_path(self, suggested: Path) -> Path | None:
        self.suggested = suggested
        return self.save_path


@pytest.fixture
def view() -> FakeView:
    return FakeView()


@pytest.fixture
def presenter(view: FakeView, sample_path: Path) -> MainPresenter:
    return MainPresenter(view, build_service(), sample_path)


def test_sample_loads_and_fills_the_view(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    assert view.pattern is not None
    assert view.pattern.file_name == "sample_pattern.txt"
    assert view.pattern.summary == "5501 points, 10.00 - 120.00 deg"
    assert (view.pattern.window_low, view.pattern.window_high) == (10.0, 120.0)
    assert len(view.pattern.difference) == 5501
    assert view.errors == []


def test_calculation_reaches_the_view_formatted(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    presenter.calculate()
    assert view.result is not None
    assert view.result.headline.value == "2.283"
    assert [m.value for m in view.result.metrics] == ["1.019", "3.60", "2.50", "2.56", "1.439"]
    assert view.result.metrics[0].hint == "Q = 1.925"
    assert view.result.metrics[1].hint == "cRwp 12.56"
    assert view.result.tone is Tone.WARNING
    assert view.result.verdict_text.endswith("Multiply them by 2.283.")
    assert "Coefficient .......... 2.2830" in view.result.report


def test_fields_left_at_their_limits_mean_the_whole_pattern(
    presenter: MainPresenter, view: FakeView
) -> None:
    presenter.open_sample()
    presenter.calculate()
    assert view.result is not None
    assert view.result.metrics[-1].hint == "N = 5501"


def test_a_narrower_window_is_passed_on(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    view.input = SettingsInput(27, 2, WeightScheme.INVERSE_INTENSITY, 20.0, 60.0)
    presenter.calculate()
    assert view.result is not None
    assert view.result.metrics[-1].hint == "N = 2001"


def test_weighting_choice_is_passed_on(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    view.input = SettingsInput(27, 2, WeightScheme.INVERSE_SQRT_INTENSITY, 10.0, 120.0)
    presenter.calculate()
    assert view.result is not None
    assert view.result.headline.value == "2.656"


def test_calculating_without_a_pattern_is_an_error(
    presenter: MainPresenter, view: FakeView
) -> None:
    presenter.calculate()
    assert view.errors == [("No pattern", "Open a pattern file first.")]
    assert view.result is None


def test_bad_settings_clear_the_old_result(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    presenter.calculate()
    view.input = SettingsInput(2, 3, WeightScheme.INVERSE_INTENSITY, 10.0, 120.0)
    presenter.calculate()
    assert view.result is None  # a stale result must not stay up
    assert view.errors[-1][0] == "Cannot calculate"
    assert "C cannot exceed P" in view.errors[-1][1]


def test_unreadable_file_keeps_the_previous_pattern(
    presenter: MainPresenter, view: FakeView, tmp_path: Path
) -> None:
    presenter.open_sample()
    broken = tmp_path / "broken.txt"
    broken.write_text("no numbers here\n")
    presenter.load(broken)
    assert view.errors[-1][0] == "Cannot open broken.txt"
    assert view.pattern is not None
    assert view.pattern.file_name == "sample_pattern.txt"
    presenter.calculate()  # still works on the old pattern
    assert view.result is not None


def test_missing_file_is_reported(presenter: MainPresenter, view: FakeView) -> None:
    presenter.load(Path("C:/no/such/file.txt"))
    assert view.errors[-1][0] == "Cannot open file.txt"
    assert view.pattern is None


def test_loading_a_new_pattern_drops_the_old_result(
    presenter: MainPresenter, view: FakeView
) -> None:
    presenter.open_sample()
    presenter.calculate()
    presenter.open_sample()
    assert view.result is None
    presenter.save_report()
    assert view.errors[-1] == ("Nothing to save", "Run the calculation first.")


def test_open_dialog_cancelled_does_nothing(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_file()
    assert view.pattern is None
    assert view.errors == []


def test_open_dialog_path_is_loaded(
    presenter: MainPresenter, view: FakeView, sample_path: Path
) -> None:
    view.open_path = sample_path
    presenter.open_file()
    assert view.pattern is not None


def test_report_is_saved_next_to_the_pattern_by_default(
    presenter: MainPresenter, view: FakeView, sample_path: Path, tmp_path: Path
) -> None:
    presenter.open_sample()
    presenter.calculate()
    view.save_path = tmp_path / "out.txt"
    presenter.save_report()
    assert view.suggested == sample_path.with_name("sample_pattern_esd.txt")
    assert view.successes == [("Report saved", str(tmp_path / "out.txt"))]
    assert "Coefficient .......... 2.2830" in (tmp_path / "out.txt").read_text("utf-8")


def test_save_dialog_cancelled_writes_nothing(presenter: MainPresenter, view: FakeView) -> None:
    presenter.open_sample()
    presenter.calculate()
    presenter.save_report()
    assert view.successes == []
    assert view.errors == []


def test_failed_save_is_reported(presenter: MainPresenter, view: FakeView, tmp_path: Path) -> None:
    presenter.open_sample()
    presenter.calculate()
    view.save_path = tmp_path / "no_such_folder" / "out.txt"
    presenter.save_report()
    assert view.errors[-1][0] == "Cannot save the report"
    assert view.successes == []
