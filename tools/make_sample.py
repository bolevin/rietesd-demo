"""Generate the synthetic demo pattern shipped with the program.

    python tools/make_sample.py

The pattern is not a measurement.  It imitates a laboratory Cu K-alpha1 scan of
a cubic perovskite with a minor second phase, "refined" with a model that is
deliberately a little wrong (peak widths, positions, intensities, asymmetry).
That misfit is what makes neighbouring residuals share their sign - the serial
correlation the program exists to detect.  The seed is fixed, so the file is
reproducible byte for byte.

The layout is the one TOPAS v.5 writes: comma-separated, column names in the
last quoted line, phase and peak curves stored with the background added.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SEED = 20261114
WAVELENGTH = 1.5406  # Cu K-alpha1, Angstrom
OUT = Path(__file__).resolve().parents[1] / "src" / "rietesd_demo" / "data" / "sample_pattern.txt"

TITLE = (
    "Synthetic demo pattern (not a measurement): cubic perovskite + minor "
    "second phase; refinement with P = 27 and C = 2"
)

# h^2 + k^2 + l^2 -> relative intensity, primitive cubic cell a = 4.045 A
PEROVSKITE_A = 4.045
PEROVSKITE = {
    1: 12,
    2: 100,
    3: 22,
    4: 35,
    5: 8,
    6: 30,
    8: 16,
    9: 4,
    10: 12,
    11: 5,
    12: 6,
    13: 2,
    14: 10,
    16: 3,
    17: 3,
    18: 6,
    19: 2,
    20: 6,
}
# face-centred cubic cell a = 10.60 A, a few strong lines only
PYROCHLORE_A = 10.60
PYROCHLORE = {12: 100, 16: 30, 32: 38, 44: 30}


def two_theta_of(a: float, n: int) -> float:
    d = a / np.sqrt(n)
    return float(2.0 * np.degrees(np.arcsin(WAVELENGTH / (2.0 * d))))


def fwhm(two_theta: float, scale: float = 1.0) -> float:
    t = np.tan(np.radians(two_theta / 2.0))
    return scale * float(np.sqrt(0.020 * t * t - 0.010 * t + 0.012))


def pseudo_voigt(
    x: np.ndarray, centre: float, width: float, eta: float, asymmetry: float = 0.0
) -> np.ndarray:
    """Unit-height pseudo-Voigt; ``asymmetry`` widens the low-angle side."""
    w = np.where(x < centre, width * (1.0 + asymmetry), width)
    u = (x - centre) / (w / 2.0)
    return eta / (1.0 + u * u) + (1.0 - eta) * np.exp(-np.log(2.0) * u * u)


def phase(
    x: np.ndarray,
    a: float,
    lines: dict[int, float],
    height: float,
    *,
    width_scale: float,
    shift: float,
    wobble: np.ndarray | None,
    asymmetric: bool,
) -> np.ndarray:
    y = np.zeros_like(x)
    for k, (n, rel) in enumerate(lines.items()):
        centre = two_theta_of(a, n)
        gain = 1.0 if wobble is None else 1.0 + wobble[k]
        asym = 0.35 * np.exp(-centre / 25.0) if asymmetric else 0.0
        y += (
            gain
            * height
            * rel
            / 100.0
            * pseudo_voigt(
                x, centre + shift, fwhm(centre, width_scale), 0.40 + 0.003 * centre, asym
            )
        )
    return y


def background(x: np.ndarray) -> np.ndarray:
    return 900.0 + 2600.0 * np.exp(-(x - 10.0) / 18.0) + 0.9 * (x - 10.0)


def main() -> None:
    rng = np.random.default_rng(SEED)
    x = np.round(np.arange(10.0, 120.0 + 1e-9, 0.02), 2)

    # what the refinement believes ---------------------------------------
    bkg = background(x)
    main_phase = phase(
        x,
        PEROVSKITE_A,
        PEROVSKITE,
        42000.0,
        width_scale=1.0,
        shift=0.0,
        wobble=None,
        asymmetric=False,
    )
    minor_phase = phase(
        x,
        PYROCHLORE_A,
        PYROCHLORE,
        1500.0,
        width_scale=1.3,
        shift=0.0,
        wobble=None,
        asymmetric=False,
    )
    hump = 420.0 * pseudo_voigt(x, 21.5, 6.0, 0.2)  # amorphous hump
    holder = 650.0 * pseudo_voigt(x, 38.47, 0.16, 0.5)  # sample-holder line
    y_calc = bkg + main_phase + minor_phase + hump + holder

    # what the sample really does ----------------------------------------
    truth = (
        bkg * (1.0 + 0.004 * np.sin((x - 10.0) / 7.0))
        + phase(
            x,
            PEROVSKITE_A,
            PEROVSKITE,
            42000.0,
            width_scale=1.045,
            shift=0.004,
            wobble=rng.normal(0.0, 0.02, len(PEROVSKITE)),
            asymmetric=True,
        )
        + phase(
            x,
            PYROCHLORE_A,
            PYROCHLORE,
            1500.0,
            width_scale=1.35,
            shift=-0.006,
            wobble=rng.normal(0.0, 0.04, len(PYROCHLORE)),
            asymmetric=True,
        )
        + 1.03 * hump
        + 0.96 * holder
    )
    y_obs = rng.poisson(truth)

    header = "'x,Yobs,Ycalc,Diff,Perovskite,Pyrochlore,Bkg,Peaks Phase:0,Peaks Phase:0"
    lines = ["'" + TITLE, header]
    for i in range(len(x)):
        calc = round(float(y_calc[i]), 4)
        row = (
            f"{x[i]:.4f}",
            f"{int(y_obs[i])}",
            f"{calc:.4f}",
            f"{int(y_obs[i]) - calc:.4f}",
            f"{bkg[i] + main_phase[i]:.4f}",
            f"{bkg[i] + minor_phase[i]:.4f}",
            f"{bkg[i]:.4f}",
            f"{bkg[i] + hump[i]:.4f}",
            f"{bkg[i] + holder[i]:.4f}",
        )
        lines.append(",".join(row))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    print(f"wrote {OUT}  ({len(x)} points, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
