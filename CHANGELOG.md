# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-14

First version.

### Added

- Durbin-Watson statistic *d*, critical value *Q* and the verdict on serial correlation.
- Coefficient for the correction of e.s.d.'s after Berar & Lelann.
- Agreement factors Rwp, Rexp, Rp and GoF, as refined and background-corrected.
- Two weighting schemes: w = 1/Yobs and w = 1/sqrt(Yobs).
- Restriction of the calculation to a 2Theta window.
- Reader for the comma-separated pattern TOPAS v.5 exports.
- Plot of the pattern with the difference curve; light and dark theme.
- Plain-text report, shown on screen and saved on request.
- Synthetic sample pattern and the script that generates it.
- `--selftest` to verify a build without opening a window.
