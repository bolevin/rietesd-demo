# 0002 — Model–View–Presenter with a passive view

Status: accepted

## Context

GUI logic written inside widget classes can only be tested by driving widgets, and tests
that drive widgets are slow, brittle and blind to most mistakes in the logic itself.

## Decision

- `ui.view.MainView` is a `Protocol`: what a window must be able to show and to ask.
- `ui.presenter.MainPresenter` takes user intents (`open_file`, `calculate`, `save_report`),
  calls the use cases and hands the view finished view models — strings already formatted.
  It imports no Qt.
- `ui.main_window.MainWindow` implements the protocol. It shows what it is given and
  forwards clicks. It contains no decision and no number formatting.

## Consequences

- The whole interaction logic, including error paths and file dialogs, is tested against a
  `FakeView` in milliseconds and without a display.
- The Qt tests that remain check wiring only: a click reaches the presenter, a view model
  reaches the right label.
- The window keeps a reference to its presenter. Qt signal connections do not keep a plain
  Python object alive; without the reference the presenter was garbage-collected and every
  button went dead — found by the first window test.
