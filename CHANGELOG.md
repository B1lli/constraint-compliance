# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-09-07

First public release.

### Added
- `SKILL.md`: the constraint-compliance gate skill. Six-section method (when to use, intent, level, rubric, goal,
  completion etiquette) with a file-based binding: goal in `.gate/goal.json`, deterministic checks via
  `scripts/gate_check.py`, independent evaluation via the host's sub-agent facility.
- `scripts/gate_check.py`: eleven deterministic validator types, fail-closed exit codes.
- `tests/test_gate_check.py`: positive and negative controls for every validator, exit-code semantics.
- `examples/rfp-response/`: a runnable end-to-end example.
- `docs/METHOD.md` (zh) and `docs/METHOD.en.md` (en): method statement, prior art, measurements, limitations.
- `docs/PROVENANCE.md`: dated design history and how to verify public timestamps.
- `docs/validators.md`: validator reference.
- Git hooks (`.githooks/`) and CI that refuse provenance markers in commits.

### Fixed
- `gate_check.py` mis-reported "no validator attached" and exited 2 when the only validator-bearing hard criterion
  could not be decided (illegal regex or unknown type). It now reports the criterion as undecided and exits 1.

[0.1.0]: https://github.com/B1lli/constraint-compliance/releases/tag/v0.1.0
