# UCF Protocol productization record

### Offline provider mapping verification

Added `examples/langfuse_adapter.py` against Langfuse's documented `create_score` signature
(inspected 2026-08-31). It previews calls without importing a vendor SDK or transmitting data.
The adapter has trace/span, session, missing-target, stable-ID and score-direction tests; CI also
runs the preview with the installed wheel. Local checks: Ruff format/lint and strict mypy pass;
`pytest -q` passes 124 tests with 94.44% branch coverage. Live delivery has not been exercised and
requires a consuming application's configured client and real project identifiers.

## 2026-08-31 interoperability checkpoint

PR #11 is merged at `c74dc18`; its follow-up persistence and timestamp fixes are preserved.
Added public `score_records()` and `export --format scores`: six raw scores with stable IDs,
direction flags, and allowlisted correlation identifiers. No external service is contacted and
free-text context, actor labels, and unrelated metadata are not exported. Tests cover identity,
direction, privacy filtering, invalid correlation values, detached output, and file/stdout CLI
equivalence. The offline provider adapter is now implemented; final release audit remains. This does
not establish live third-party interoperability or validated market demand.

Last updated: 2026-08-31

## Historical pre-productization assessment

The repository contains useful ideas and partial implementations for six coordination-health signals, text/JSON formatting, and SQLite history. Its current release claims are not supported by the checked-in product:

- `python -m pytest` collected 111 tests but failed 4; many of the 107 passing tests catch all exceptions or only assert when an API happens to exist.
- `python -m build` succeeded but the wheel contained the test suite and metadata, not the UCF implementation.
- the README points to a missing `src` coverage target, a missing CI workflow, a missing development requirements file, and an MIT license even though `LICENSE` is Apache-2.0.
- the dashboard module imports a package hierarchy, analytics engine, and web dependencies that do not exist here.
- several examples call APIs and classes that are not implemented in this repository.
- much of the documentation describes `helix-unified` production infrastructure rather than this repository.
- metric names, units, and ranges disagree across modules and documentation.

The worktree was clean on `main` at `5190823f16c32a68ef9109bd7b59611a727572cf` before productization began. `main` matched `origin/main`; no user changes or untracked files required preservation.

## Chosen product definition

UCF Protocol will be a local-first Python protocol, library, and CLI for recording explicit coordination-health observations. It will:

1. define one versioned JSON representation for six dimensionless signals;
2. validate observations strictly and calculate a transparent phase and composite score;
3. persist observations in a local SQLite journal with duplicate-event protection;
4. let a user record, inspect, validate, list, and export observations through the `ucf` CLI;
5. work without hosted Samsarix or legacy Helix services, accounts, credentials, network access, or third-party runtime packages.

The signals are user-supplied operational assessments, not scientific measurements of consciousness and not substitutes for service-level telemetry. This limitation is part of the product contract.

## Target user and primary use case

The target user is a developer or operator prototyping a human/agent workflow who wants a small, auditable coordination scorecard alongside ordinary logs and telemetry.

The primary journey is:

1. install the package in a virtual environment;
2. initialize or implicitly create a local journal;
3. record one valid six-signal observation;
4. read the latest state and recent history;
5. export versioned JSON Lines for analysis or integration.

The journey must also handle an empty journal, invalid/non-finite metrics, duplicate event IDs, database errors, bounded history queries, stdout export, safe file export, and machine-readable JSON output.

## Key product and architecture decisions

- Use a `src/` package layout so tests and consumers exercise installed code rather than accidental repository-root imports. This follows current PyPA guidance.
- Use only the Python standard library at runtime. SQLite is appropriate for the local journal and avoids operating cost or service setup.
- Normalize all six metrics to finite numbers in `[0, 1]`. `friction` is inverse (lower is better); all other dimensions are positive.
- Keep canonical English names (`harmony`, `resilience`, `throughput`, `focus`, `friction`, `velocity`) and accept legacy aliases only at the parsing boundary.
- Use `ucf/v1` plus JSON Schema Draft 2020-12 for a stable exchange contract.
- Model each observation as a point-in-time gauge-like event with a timestamp and optional bounded attributes. UCF does not claim compatibility with OpenTelemetry, but follows its emphasis on explicit names, units, timestamps, and unambiguous point semantics.
- Use parameterized SQLite queries, schema-level range checks, short-lived connections, a busy timeout, and idempotent event IDs.
- Package version is `1.0.0rc1`: the repository previously claimed 1.0.0, but no `ucf-protocol` project was present on PyPI during the audit and the old wheel did not contain the implementation. Publication remains owner-controlled.

## Assumptions

- The six-metric idea and Apache-2.0 file reflect the repository's intended reusable core.
- A local CLI/library is more defensible than recreating the private/live Helix service documented elsewhere.
- The repository does not need authentication because the supported product opens no network listener and operates only with the invoking user's filesystem privileges.
- Metadata may contain private user content, so the product will not transmit it or enable telemetry by default.
- Existing licensing files express owner intent but contain positioning that needs owner/legal confirmation before publication; this work does not select or rewrite legal terms.
- Samsarix is the current maintainer brand and Samsarix LLC is the owner-confirmed company name.
  `contact@samsarix.com` and `support@samsarix.com` are owner-confirmed working contact channels.

## Baseline command results

Run on Windows with Python 3.11.9 before implementation:

| Command | Result |
| --- | --- |
| `git status --short --branch --untracked-files=all` | Passed; clean `main...origin/main`. |
| `python --version` | Passed; Python 3.11.9. |
| `python -m compileall -q .` | Passed, but compilation did not exercise imports or runtime paths. |
| `python -m pytest` | Failed: 4 failed, 107 passed in 10.38s. |
| `python -m build` | Exited 0 with metadata warnings; built an unusable wheel containing tests rather than the UCF modules. |
| `python -m pip check` | Failed because the shared interpreter has unrelated package conflicts. This is environment evidence, not a repository dependency result. |

There were no real repository lint, format, or type-check configurations to run at baseline. The README's claimed GitHub Actions, flake8, mypy, Bandit, Safety, and Codecov pipeline was absent.

## Historical baseline findings and priorities

### P0

- The built distribution does not contain the product.
- The documented quick-start API and examples do not exist.
- The primary tests are partly non-asserting and the suite is red.
- Product identity depends on unrelated `helix-unified` infrastructure.
- No complete first-run-to-persist-to-read journey exists.

### P1

- Metric names, units, ranges, phases, and composite scores conflict across modules.
- SQLite code lacks strict input validation, consistent error contracts, bounded queries, and duplicate-event handling.
- Several modules are dead, import missing private components, or advertise unsupported production features.
- Documentation contains fabricated or unverifiable deployment, API, monitoring, and readiness claims.
- There is no CI workflow, package-shape test, CLI test, formatter/linter configuration, or type-check configuration.
- Runtime requirements include numerous unused packages; optional code fails unclearly when its dependency is absent.
- Licensing narrative and legal files need owner/legal reconciliation before public release.

### P2

- Add adapters for OpenTelemetry or CSV only after real user demand.
- Add retention/compaction controls if journals become large in practice.
- Add signed releases and automated publication after the owner configures trusted publishing.
- Add richer analysis only after the scoring model is validated with users.

## Implementation checklist

- [x] Replace the flat collection of modules with an installable `src/ucf_protocol` package.
- [x] Define and document `ucf/v1`, strict validation, phases, and score calculation.
- [x] Implement the SQLite journal and idempotent event recording.
- [x] Implement `ucf init`, `record`, `status`, `history`, `summary`, `validate`, and `export`.
- [x] Replace permissive tests with focused unit, integration, CLI, and package-shape tests.
- [x] Remove dead hosted-service code, placeholders, and misleading examples.
- [x] Add deterministic build metadata, lint/type/test configuration, and CI.
- [x] Rewrite README, API, architecture, quick-start, deployment, security, community, and contribution guidance.
- [x] Complete the repository-wide security scan and record its result.
- [x] Verify the wheel in a clean virtual environment.

## Release acceptance criteria

- A clean environment can build and install the wheel.
- The installed `ucf` command exposes `--help` and `--version`.
- The complete primary journey works using only documented commands.
- Invalid and non-finite values are rejected without creating a record.
- Duplicate event IDs are visible and do not create duplicate rows.
- Empty, success, and ordinary database/file failures have clear messages and meaningful exit codes.
- Unit, integration, CLI, lint, format, type-check, build, metadata, and installed-wheel smoke checks pass.
- CI runs the meaningful checks on supported Python versions.
- Every shipped example is executed by tests or CI.
- Documentation describes only implemented behavior and no locally actionable P0 remains.

## Completed work

- Protected and inventoried the clean worktree, recent history, branches, and remotes.
- Reviewed the source, tests, examples, configuration, and documentation inventory.
- Ran and recorded the actual baseline commands above.
- Performed bounded current research against PyPA packaging guidance, Python SQLite documentation, OpenTelemetry's metric data model/semantic naming guidance, and JSON Schema Draft 2020-12.
- Selected the local-first protocol/library/CLI product wedge.
- Replaced the non-installable flat modules with a typed `src/` package and a real console entry point.
- Implemented immutable bounded observations, a packaged JSON Schema, SQLite persistence, summaries, strict JSON import, and safe JSONL export.
- Added explicit duplicate, empty, invalid, storage, broken-pipe, and interruption behavior.
- Replaced non-asserting tests with 91 focused tests and a 90% branch-coverage gate.
- Removed 15,000+ lines of dead modules, placeholders, unrelated infrastructure guides, and unsupported examples while preserving legal and repository instruction files.
- Added pinned least-privilege CI across Python 3.10-3.14, dependency update configuration, and a distribution smoke job.
- Rewrote product, API, metrics, architecture, operations, security, contribution, community, and ethical guidance to match implemented behavior.
- Updated package and community ownership to the Samsarix brand and Samsarix LLC legal company,
  configured private security and conduct reporting through the owner-confirmed mailboxes, and
  removed obsolete Helix licensing contacts without changing substantive license terms.
- Built and inspected the sdist and wheel from an isolated build, validated both with Twine, and installed the exact wheel into a clean virtual environment.
- Published the productization commits to draft pull request #6 and passed the hosted GitHub Actions
  matrix on Python 3.10 through 3.14 plus the distribution smoke job.
- Completed a standard repository-wide security scan over all 36 final files. One local export race candidate was validated and suppressed because no privilege or tenant boundary exists; no reportable vulnerability or deferred security work remained. The canonical scan report is outside the repository under the system temporary security-scan directory and is linked in the delivery handoff.
- Verified and addressed all seven inline findings from the merged productization review: disabled
  persisted CI credentials, documented example setup, bounded file reads, closed export connections
  between bounded batches, removed phase-definition drift, aligned schema/parser requirements, and
  normalized invalid message-type errors. Also corrected the commercial-license narrative so it does
  not contradict the Apache-2.0 package grant.
- Researched current evaluation and tracing platforms, selected a complementary local-first
  assessment and release-gating wedge, and documented the product boundary and non-goals.
- Added deterministic baseline/candidate comparisons, direction-aware metric deltas, explicit
  average-value quality policies, stable machine-readable results, and CI exit code 5.
- Documented a vendor-neutral correlation metadata convention for traces, spans, sessions,
  experiments, releases, and evaluators.
- Added bounded atomic JSONL import with rollback-on-error, dry-run, and explicit duplicate
  policies; packaged a manifest-driven valid, invalid, boundary, and correlation fixture suite.
- Added and executed an end-to-end release-gate example, and hardened simultaneous first-open
  SQLite initialization after the full suite exposed a WAL mode-change race.

## Final local verification

Run on Windows with Python 3.11.9 in an isolated development environment:

| Check | Result |
| --- | --- |
| `python -m compileall -q src tests examples` | Passed. |
| `ruff format --check src tests examples` | Passed; 17 files already formatted. |
| `ruff check src tests examples` | Passed; no findings. |
| `mypy src` | Passed in strict mode; 7 source files checked. |
| `pytest` | Passed: 113 tests, 94.24% branch coverage. |
| `python -m build --outdir .artifacts/dist-final` | Passed; isolated sdist-to-wheel build. |
| `python -m twine check .artifacts/dist-final/*` | Passed for wheel and sdist. |
| Clean-wheel `pip check` | Passed; no broken requirements and no runtime dependencies. |
| Installed `ucf --version` / `--help` | Passed; reported `1.0.0rc1` and all ten commands. |
| Installed record/status/export/schema journey | Passed against a fresh SQLite journal. |
| `python examples/basic_journey.py` | Passed using the installed public API. |

## Hosted verification

GitHub Actions run `30413304310` for draft pull request #6 passed the distribution smoke job and all
five supported interpreters: Python 3.10, 3.11, 3.12, 3.13, and 3.14. CodeRabbit reported success
with its review intentionally skipped while the pull request remains a draft.

## Release disposition

The repository is locally ready for review as `1.0.0rc1`: the primary journey, failure paths,
distribution, metadata, installed wheel, example, and security scan are evidenced. It is not ready
for public general availability or package publication until the owner resolves the license
positioning, reviews and merges the changes, and intentionally configures publishing/signing. Durable
private security and conduct contacts are documented through the working Samsarix mailboxes, and the
hosted supported-Python CI matrix has passed.

## Deferred work and rationale

- Hosted APIs, dashboards, WebSockets, auth, Redis, PostgreSQL, Kubernetes, cloud deployment, and external integrations are out of scope because the repository has no working implementation and the local product does not require them.
- Predictive or ML analytics are out of scope because the repository contains no validated model or evaluation evidence.
- Scientific or metaphysical claims about consciousness are out of scope; observations are explicitly subjective operational inputs.

## Owner-, credential-, legal-, store-, or production-blocked tasks

- Confirm public licensing positioning across `LICENSE`, `LICENSE.PROPRIETARY`, and `LICENSING.md` with the owner/legal counsel.
- Decide whether and where to publish the distribution; configure PyPI trusted publishing if desired.
- Create signing/provenance policy and release credentials if public artifacts will be signed.

## Known risks

- The composite score is a transparent heuristic, not an empirically validated operational predictor.
- SQLite is suitable for a local journal, not a shared multi-host coordination database.
- User-supplied metadata may contain sensitive information; local-only behavior reduces but does not eliminate filesystem exposure.
- Reframing the repository as a focused protocol intentionally removes compatibility with undocumented, unshipped examples.

## Distribution and sustainability

The simplest distribution is a pure-Python wheel and source distribution published to PyPI after owner approval. Until then, installation from a tagged Git checkout is sufficient. The core has zero hosted operating cost and no runtime API spend. Sustainable support could come from maintenance sponsorship, consulting, or paid integration work, but no pricing or demand is assumed or validated here.

## Research references

- PyPA, `pyproject.toml` and console-script specification: <https://packaging.python.org/en/latest/specifications/pyproject-toml/>
- PyPA, source-layout tradeoffs: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>
- Python 3.14 `sqlite3` documentation: <https://docs.python.org/3/library/sqlite3.html>
- OpenTelemetry Metrics data model: <https://opentelemetry.io/docs/specs/otel/metrics/data-model/>
- OpenTelemetry metric semantic conventions: <https://opentelemetry.io/docs/specs/semconv/general/metrics/>
- JSON Schema Draft 2020-12: <https://json-schema.org/draft/2020-12>
