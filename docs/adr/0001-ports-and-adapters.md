# 0001 — Ports and adapters around a pure domain

Status: accepted

## Context

The value of the program is a calculation. Everything else — the file format, the report
layout, the window — is likely to change, and none of it should be able to alter a number.

## Decision

Four layers, dependencies pointing inwards:

- `domain` holds the calculation as immutable values and pure functions. It imports the
  standard library and nothing else.
- `application` holds the use cases and declares, as `Protocol`s, what they need from the
  outside: `PatternReader`, `ReportRenderer`, `TextStore`.
- `adapters` and `ui` implement those needs.
- `main` is the only module that names concrete classes and wires them together.

## Consequences

- The calculation is tested with plain values, the use cases with in-memory fakes.
- A new input format or report layout is one new adapter; no existing module changes.
- More files than a single-module script would need. Accepted: the boundaries are the point.
- The rule decays unless enforced, hence [ADR 0007](0007-architecture-rules-as-tests.md).
