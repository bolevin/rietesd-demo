# 0007 — Architecture rules are tests

Status: accepted

## Context

A layering rule that lives only in a document holds until the first deadline. One
convenient import of numpy into the calculation, or of a Qt class into the presenter, and
the properties the architecture was chosen for are gone without any test turning red.

## Decision

State the rules as [import-linter](https://import-linter.readthedocs.io) contracts in
`pyproject.toml` and run them in the test suite and as a CI step:

1. dependencies point inwards (`main` → `ui` | `adapters` → `application` → `domain`);
2. `domain` and `application` import nothing outside the standard library;
3. `ui.presenter` and `ui.view` import no Qt.

A second test reads the import statements of `domain` directly, independent of the tool.

## Consequences

- Breaking a rule fails the build with the offending import named.
- The rules themselves are tested: `tools/mutation_check.py` adds a forbidden import to the
  domain and to the presenter and expects the suite to fail.
- One more development dependency.
