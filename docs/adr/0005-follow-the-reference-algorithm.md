# 0005 — Follow the reference algorithm literally

Status: accepted

## Context

Porting the Bérar–Lelann procedure from the reference program exposed three details that a
fresh implementation from the paper might do differently:

1. For a pair of correlated neighbours, both squared residuals are normalised with the
   uncertainty of the *earlier* point.
2. π is written as `3.14159`.
3. A point is added to the corrected sum when its successor arrives, so the last point of
   the scan enters the plain sum only.

## Decision

Keep all three. The demo demonstrates RietESD; it must give RietESD's numbers. Whether any
of these should change is a question for the author of the method, not for a port.

## Consequences

- The demo agrees with the full program (ADR 0004).
- Each detail is visible and explained where it occurs in `domain/berar.py`.
- Detail 1 is held by the golden master (`tools/mutation_check.py` breaks it and the test
  fails). Detail 3 is held by hand-worked tests in `tests/domain/test_berar.py`.
- Detail 2 is **not** held by any test and cannot be: using `math.pi` moves the coefficient
  by about 4 × 10⁻⁸, less than the single-precision reference can resolve. It is kept for
  traceability to the reference.
- The effect of detail 3 is of order 1/N — negligible for a real pattern, noticeable in the
  five-point examples of the tests, where it is spelled out.
