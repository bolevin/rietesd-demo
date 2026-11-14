"""Reader for the comma-separated pattern TOPAS v.5 exports.

Layout::

    'free-text title                           (optional)
    'x,Yobs,Ycalc,Diff,Phase 1,...,Bkg,...     (column names: last text line)
    10.0000,3562,3505.6163,56.3837,...,3500.0000,...

The first column is 2Theta and the second Yobs, whatever they are called;
``Ycalc``, ``Diff`` and ``Bkg`` are found by name.  One of Ycalc and Diff may be
missing (it is derived from the other); every other column is ignored.
"""

from __future__ import annotations

import math
from pathlib import Path

from rietesd_demo.application.ports import PatternFormatError
from rietesd_demo.domain import Pattern

_QUOTES = "'\" "


def _numbers(line: str) -> list[float] | None:
    """The line as a row of finite numbers, or None if it is text."""
    cells = line.split(",")
    if len(cells) < 2:
        return None
    try:
        values = [float(c) for c in cells]
    except ValueError:
        return None
    return values if all(math.isfinite(v) for v in values) else None


def _split(text: str) -> tuple[str, str, list[list[float]]]:
    """Title, column-name line and data rows of the file."""
    title = ""
    header: str | None = None
    rows: list[list[float]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        values = _numbers(stripped)
        if values is None:
            if rows:
                raise PatternFormatError(f"Line {number}: text in the middle of the data.")
            if header is not None and not title and "," not in header:
                title = header
            header = stripped.strip(_QUOTES)
        elif rows and len(values) != len(rows[0]):
            raise PatternFormatError(
                f"Line {number}: {len(values)} values, expected {len(rows[0])}."
            )
        else:
            rows.append(values)

    if not rows:
        raise PatternFormatError("No rows of comma-separated numbers were found.")
    if header is None or "," not in header:
        raise PatternFormatError(
            "The line with the column names (x,Yobs,Ycalc,Diff,...,Bkg) is missing."
        )
    return title, header, rows


class TopasReader:
    """Implements :class:`rietesd_demo.application.ports.PatternReader`."""

    def read(self, path: Path) -> Pattern:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return self.parse(text)

    def parse(self, text: str) -> Pattern:
        title, header, rows = _split(text)
        names = [name.strip().lower() for name in header.split(",")]
        if len(names) != len(rows[0]):
            raise PatternFormatError(
                f"{len(names)} column names but {len(rows[0])} columns of data."
            )

        def column(index: int) -> tuple[float, ...]:
            return tuple(row[index] for row in rows)

        def find(name: str) -> int | None:
            return names.index(name) if name in names[2:] else None

        i_calc, i_diff, i_bkg = find("ycalc"), find("diff"), find("bkg")
        if i_bkg is None:
            raise PatternFormatError("The background column (Bkg) is missing.")
        y_obs = column(1)
        if i_calc is not None:
            y_calc = column(i_calc)
        elif i_diff is not None:
            y_calc = tuple(o - d for o, d in zip(y_obs, column(i_diff), strict=True))
        else:
            raise PatternFormatError("Neither Ycalc nor Diff is present.")

        return Pattern(
            two_theta=column(0),
            y_obs=y_obs,
            y_calc=y_calc,
            background=column(i_bkg),
            title=title,
        )
