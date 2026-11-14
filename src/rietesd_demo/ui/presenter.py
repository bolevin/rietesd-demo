"""Presenter: turns user intent into use-case calls and results into view models."""

from __future__ import annotations

import math
from pathlib import Path

from rietesd_demo.application import (
    AnalysisRun,
    AnalysisService,
    LoadedPattern,
    PatternFormatError,
)
from rietesd_demo.domain import AnalysisSettings, Correlation, DomainError
from rietesd_demo.ui.view import (
    MainView,
    Metric,
    PatternViewModel,
    ResultViewModel,
    SettingsInput,
    Tone,
)

#: Decimals of the 2Theta window fields; the offered limits are rounded outwards
#: to this precision so that the default window always holds the whole pattern.
WINDOW_DECIMALS = 3

_VERDICT = {
    Correlation.POSITIVE: (
        "Positive serial correlation",
        "d < Q: the e.s.d.'s from the refinement are underestimated. "
        "Multiply them by {coefficient}.",
        Tone.WARNING,
    ),
    Correlation.NONE: (
        "No serial correlation",
        "Q <= d <= 4 - Q: the e.s.d.'s from the refinement can be used as they are.",
        Tone.GOOD,
    ),
    Correlation.NEGATIVE: (
        "Negative serial correlation",
        "d > 4 - Q: neighbouring residuals alternate in sign. Berar's correction "
        "does not apply; check the weights and the step of the scan.",
        Tone.WARNING,
    ),
}


class MainPresenter:
    def __init__(self, view: MainView, service: AnalysisService, sample: Path) -> None:
        self._view = view
        self._service = service
        self._sample = sample
        self._loaded: LoadedPattern | None = None
        self._run: AnalysisRun | None = None

    # ---- user intents --------------------------------------------------
    def open_file(self) -> None:
        path = self._view.ask_open_path()
        if path is not None:
            self.load(path)

    def open_sample(self) -> None:
        self.load(self._sample)

    def load(self, path: Path) -> None:
        try:
            loaded = self._service.load(path)
        except (OSError, PatternFormatError, DomainError) as error:
            self._view.show_error(f"Cannot open {path.name}", str(error))
            return
        self._loaded, self._run = loaded, None
        self._view.clear_result()
        self._view.show_pattern(_pattern_view_model(loaded))

    def calculate(self) -> None:
        if self._loaded is None:
            self._view.show_error("No pattern", "Open a pattern file first.")
            return
        try:
            settings = self._settings(self._view.settings(), self._loaded)
            run = self._service.analyse(self._loaded, settings)
        except (ValueError, DomainError) as error:
            self._run = None
            self._view.clear_result()
            self._view.show_error("Cannot calculate", str(error))
            return
        self._run = run
        self._view.show_result(_result_view_model(run, self._service.report(run)))

    def save_report(self) -> None:
        if self._run is None:
            self._view.show_error("Nothing to save", "Run the calculation first.")
            return
        suggested = self._run.source.with_name(self._run.source.stem + "_esd.txt")
        path = self._view.ask_save_path(suggested)
        if path is None:
            return
        try:
            self._service.export(self._run, path)
        except OSError as error:
            self._view.show_error("Cannot save the report", str(error))
            return
        self._view.show_success("Report saved", str(path))

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _settings(raw: SettingsInput, loaded: LoadedPattern) -> AnalysisSettings:
        low, high = _window_limits(loaded)
        return AnalysisSettings(
            n_parameters=raw.n_parameters,
            n_constraints=raw.n_constraints,
            weighting=raw.weighting,
            # a field left at its limit means "no limit on this side"
            two_theta_min=None if raw.two_theta_min <= low else raw.two_theta_min,
            two_theta_max=None if raw.two_theta_max >= high else raw.two_theta_max,
        )


def _window_limits(loaded: LoadedPattern) -> tuple[float, float]:
    scale = 10**WINDOW_DECIMALS
    first, last = loaded.pattern.two_theta[0], loaded.pattern.two_theta[-1]
    return math.floor(first * scale) / scale, math.ceil(last * scale) / scale


def _pattern_view_model(loaded: LoadedPattern) -> PatternViewModel:
    p = loaded.pattern
    low, high = _window_limits(loaded)
    return PatternViewModel(
        file_name=loaded.source.name,
        title=p.title,
        summary=f"{len(p)} points, {p.two_theta[0]:.2f} - {p.two_theta[-1]:.2f} deg",
        two_theta=p.two_theta,
        y_obs=p.y_obs,
        y_calc=p.y_calc,
        background=p.background,
        difference=p.difference,
        window_low=low,
        window_high=high,
    )


def _result_view_model(run: AnalysisRun, report: str) -> ResultViewModel:
    r, f = run.result, run.result.factors
    coefficient = f"{r.esd_coefficient:.3f}"
    title, text, tone = _VERDICT[r.correlation]
    return ResultViewModel(
        headline=Metric("e.s.d. coefficient", coefficient, "Berar & Lelann"),
        metrics=(
            Metric("Durbin-Watson d", f"{r.durbin_watson:.3f}", f"Q = {r.critical_value:.3f}"),
            Metric("Rwp, %", f"{f.r_wp:.2f}", f"cRwp {f.r_wp_bkg:.2f}"),
            Metric("Rexp, %", f"{f.r_exp:.2f}", f"cRexp {f.r_exp_bkg:.2f}"),
            Metric("Rp, %", f"{f.r_p:.2f}", f"cRp {f.r_p_bkg:.2f}"),
            Metric("GoF", f"{f.gof:.3f}", f"N = {r.n_points}"),
        ),
        verdict_title=title,
        verdict_text=text.format(coefficient=coefficient),
        tone=tone,
        report=report,
    )
