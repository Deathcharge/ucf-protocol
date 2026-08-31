# Changelog

This project follows [Semantic Versioning](https://semver.org/). Dates use ISO 8601.

## [1.0.0rc1] - 2026-07-28

### Added

- Local-only long-form score export with stable per-metric IDs, explicit score direction, and
  allowlisted correlation metadata for evaluation-platform adapters.

- Installable, typed `src/ucf_protocol` package with no third-party runtime dependencies.
- Strict immutable `ucf/v1` observation model and packaged JSON Schema 2020-12 contract.
- SQLite journal with duplicate-event protection, bounded queries, summary, and JSONL iteration.
- Ten `ucf` CLI commands: `init`, `record`, `status`, `history`, `summary`, `validate`, `export`,
  `import`, `compare`, and `check`.
- Explicit exit-code contract, bounded input and metadata, atomic file export, and clear empty state.
- Deterministic baseline/candidate comparison and explicit average-value quality gates for CI.
- Atomic bounded JSONL import with dry-run and explicit duplicate policies.
- Packaged canonical-schema, parser-compatibility, valid, invalid, boundary, and correlation
  conformance fixtures.
- Cross-version CI, strict static checks, branch coverage gate, distribution checks, and wheel smoke
  installation.

### Changed

- Unified all metrics to finite values in `[0, 1]` and documented the score and phase formulas.
- Reframed UCF as subjective coordination-health observations rather than consciousness measurement.
- Replaced legacy flat modules and hosted-service examples with a coherent local product surface.
- Updated the maintainer brand to Samsarix, identified Samsarix LLC as the legal company, and
  documented working private support and conduct channels.
- Aligned the parser and packaged schema required fields and added drift tests for phase definitions.
- Made file validation and journal export bounded across path replacement and partial iteration.
- Clarified that Apache-2.0 permits commercial use and that Samsarix commercial services or
  alternative terms are optional.
- Disabled persisted checkout credentials in CI jobs that install repository-controlled code.

### Removed

- Placeholder dashboards, unrelated hosted-infrastructure documentation, nonfunctional examples,
  and permissive tests that did not verify behavior.

### Release note

This is a release candidate. Publication, signing, and license-positioning decisions remain
maintainer-controlled gates.
