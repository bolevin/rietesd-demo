# 0004 — Double precision, verified by a golden master against the full program

Status: accepted

## Context

The original RietESD is a QuickBASIC program working in single precision. The full Python
edition reproduces its printed output digit for digit and therefore emulates single
precision operation by operation. The demo has no listing to reproduce — but its numbers
must still be demonstrably right.

## Decision

- Calculate in ordinary double precision; sum with `math.fsum`.
- Do not share code with the full program. Instead, record what the full program computes
  for the bundled pattern (`tools/make_golden.py` → `tests/golden/sample_reference.json`)
  and require the demo to agree (`tests/domain/test_golden.py`).
- The tolerance is 5 × 10⁻⁷ relative: the reference values are single precision and carry
  about seven significant digits.

## Consequences

- The calculation reads like the formulas, with no precision emulation in the way.
- Agreement between two independent implementations is evidence for both.
- The test needs only this repository; re-recording the reference needs the full program.
  The JSON stores the SHA-256 of the pattern, and a test fails if the pattern changes
  without the reference being recorded again.
- Differences below seven digits cannot be detected. Measured agreement is about 10⁻⁸.
