"""The analysis as a plain-text report."""

from __future__ import annotations

import textwrap

from rietesd_demo import __version__
from rietesd_demo.application.service import AnalysisRun
from rietesd_demo.domain import Correlation

_RULE = "=" * 68

_VERDICT = {
    Correlation.POSITIVE: "positive serial correlation (d < Q)",
    Correlation.NONE: "no serial correlation (Q <= d <= 4 - Q)",
    Correlation.NEGATIVE: "negative serial correlation (d > 4 - Q)",
}

_ADVICE = {
    Correlation.POSITIVE: (
        "The e.s.d.'s printed by the refinement are underestimated.",
        "Multiply them by the coefficient above.",
    ),
    Correlation.NONE: (
        "The residuals show no serial correlation at the 0.1 % level;",
        "the e.s.d.'s printed by the refinement can be used as they are.",
    ),
    Correlation.NEGATIVE: (
        "Neighbouring residuals alternate in sign.  Berar's correction does",
        "not apply; check the weights and the step of the scan.",
    ),
}


def _line(label: str, value: str) -> str:
    return f"  {label + ' ':.<22} {value}"


def _wrapped(label: str, value: str) -> list[str]:
    """A long value continues on the next lines, aligned under its start."""
    first, *rest = textwrap.wrap(value, width=43) or ["-"]
    return [_line(label, first), *(" " * 25 + text for text in rest)]


class PlainTextReport:
    """Implements :class:`rietesd_demo.application.ports.ReportRenderer`."""

    def render(self, run: AnalysisRun) -> str:
        s, r, f = run.settings, run.result, run.result.factors
        low, high = r.two_theta_range
        out = [
            f"RietESD Demo {__version__} - analysis report",
            _RULE,
            "",
            "Input",
            _line("File", run.source.name),
            *_wrapped("Title", run.pattern.title),
            _line("Points used, N", str(r.n_points)),
            _line("2Theta range", f"{low:.4f} - {high:.4f} deg"),
            _line("Refined parameters, P", str(s.n_parameters)),
            _line("Constraints, C", str(s.n_constraints)),
            _line("Weights", f"w = {s.weighting.value}"),
            "",
            "Serial correlation (Durbin-Watson test)",
            _line("d", f"{r.durbin_watson:.4f}"),
            _line("Q", f"{r.critical_value:.4f}"),
            _line("Verdict", _VERDICT[r.correlation]),
            "",
            "Correction of e.s.d.'s (Berar & Lelann)",
            _line("Coefficient", f"{r.esd_coefficient:.4f}"),
            *(f"  {text}" for text in _ADVICE[r.correlation]),
            "",
            "Agreement factors",
            f"  {'':22} {'as refined':>12} {'bkg-corrected':>15}",
            f"  {'Rwp, % ':.<22} {f.r_wp:>12.3f} {f.r_wp_bkg:>15.3f}",
            f"  {'Rexp, % ':.<22} {f.r_exp:>12.3f} {f.r_exp_bkg:>15.3f}",
            f"  {'Rp, % ':.<22} {f.r_p:>12.3f} {f.r_p_bkg:>15.3f}",
            f"  {'GoF ':.<22} {f.gof:>12.3f}",
            "",
            _RULE,
            "Method: J.-F. Berar & P. Lelann, J. Appl. Cryst. 24 (1991) 1-5;",
            "        R. J. Hill & H. D. Flack, J. Appl. Cryst. 20 (1987) 356-361.",
            "",
        ]
        return "\n".join(out)
