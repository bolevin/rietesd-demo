# 0003 — QFluentWidgets for the interface; GPL-3.0-or-later as a consequence

Status: accepted

## Context

The program should look at home on Windows 11 and match the full RietESD program, which
uses PySide6 with the QFluentWidgets component library.

## Options

1. **PySide6 + QFluentWidgets.** Windows 11 look out of the box, light and dark themes.
   QFluentWidgets is GPL-3.0.
2. **Plain PySide6 with a hand-written style sheet.** PySide6 is LGPL, so a permissive
   licence would be possible; the look would have to be built and maintained by hand.

## Decision

Option 1.

## Consequences

- The program as a whole is GPL-3.0-or-later. It may be used for any purpose, including
  commercially; derivatives must stay open under the same terms; an executable may only be
  passed on together with its source.
- A "non-commercial use only" licence is not possible: the GPL forbids adding restrictions.
- The dependency is confined to `ui.main_window` and `ui.plot`. The calculation, the use
  cases and the presenter do not import it (checked, see ADR 0007), so replacing the widget
  library would not touch them.
