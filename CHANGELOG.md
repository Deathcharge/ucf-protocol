# Changelog

This project follows [Semantic Versioning](https://semver.org/). Dates use ISO 8601.

## [1.0.0rc1] - 2026-07-28

### Added

- Installable, typed `src/ucf_protocol` package with no third-party runtime dependencies.
- Strict immutable `ucf/v1` observation model and packaged JSON Schema 2020-12 contract.
- SQLite journal with duplicate-event protection, bounded queries, summary, and JSONL iteration.
- `ucf` CLI commands: `init`, `record`, `status`, `history`, `summary`, `validate`, and `export`.
- Explicit exit-code contract, bounded input and metadata, atomic file export, and clear empty state.
- Cross-version CI, strict static checks, branch coverage gate, distribution checks, and wheel smoke
  installation.

### Changed

- Unified all metrics to finite values in `[0, 1]` and documented the score and phase formulas.
- Reframed UCF as subjective coordination-health observations rather than consciousness measurement.
- Replaced legacy flat modules and hosted-service examples with a coherent local product surface.

### Removed

- Placeholder dashboards, unrelated hosted-infrastructure documentation, nonfunctional examples,
  and permissive tests that did not verify behavior.

### Release note

This is a release candidate. Publication, signing, support-channel, and license-positioning decisions
remain maintainer-controlled gates.
