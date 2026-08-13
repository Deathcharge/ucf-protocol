# CLI and Python API

## Command-line interface

Global options must appear before the subcommand:

```text
ucf [--database PATH] <command> [options]
```

| Command | Purpose | Empty-journal behavior |
| --- | --- | --- |
| `init` | Create or migrate the local SQLite journal | Reports zero rows |
| `record` | Validate and insert one observation | Creates the first row |
| `status` | Show the latest observation | Exit 3 with next-step guidance |
| `history` | Show up to 1,000 recent observations | Success with an empty result |
| `summary` | Aggregate up to 1,000 recent observations | Success with an empty result |
| `compare` | Compare baseline and candidate time windows | Exit 2 if either window is empty |
| `check` | Apply explicit thresholds to recent observations | Exit 2 if the journal is empty |
| `validate` | Validate a complete `ucf/v1` JSON object | Does not open a journal |
| `import` | Atomically import bounded `ucf/v1` JSON Lines | Exit 2 for empty or invalid input |
| `export` | Stream all rows as JSON Lines | Success with empty output |

Run `ucf <command> --help` for all flags. `record` accepts either a complete object through
`--input PATH` (use `-` for stdin), or all six metric flags. Input mode cannot be mixed with field
overrides.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success, including a handled broken output pipe |
| `1` | Journal or operating-system failure |
| `2` | Invalid observation, JSON, input size, query limit, or destination state |
| `3` | `status` requested from an empty journal |
| `4` | Duplicate event ID |
| `5` | A valid `check` policy did not pass |
| `130` | Interrupted by the user |

Argument parser errors use argparse's standard exit code 2.

### Bounds and safe defaults

- File/stdin observation input is limited to 65,536 UTF-8 bytes.
- JSONL import is limited to 10 MiB, 10,000 non-blank observations, and 65,536 bytes per line.
- Metadata is a JSON object limited to 16,384 encoded bytes, 256 items per collection, and eight
  nesting levels.
- Context is limited to 512 characters; agent labels to 128 characters.
- History and summary limits are integers from 1 through 1,000.
- Export does not overwrite an existing path without `--force`.
- SQL values use parameter binding. Event IDs are primary keys.

### Atomic JSONL import

Import consumes one complete `ucf/v1` object per non-blank line. The default duplicate policy is
`error`: any duplicate rolls back the entire batch. `--on-duplicate skip` retains the first new
event and reports existing or repeated IDs as skipped. `--dry-run` performs the same transaction and
validation but rolls it back.

```console
ucf --database assessments.db import observations.jsonl --dry-run --json
ucf --database assessments.db import observations.jsonl --on-duplicate skip --json
```

The result contains `processed`, `recorded`, `skipped`, and `dry_run`. A dry run's `recorded` value
means rows that would be inserted; the journal remains unchanged. A dry run targeting a journal that
does not yet exist validates against an in-memory journal and does not create the database or parent
directories. Malformed JSONL is rejected before the journal is opened.

### Compare and gate a candidate

`compare` uses inclusive, timezone-aware ISO 8601 windows and reports candidate-minus-baseline
deltas. Raw friction delta preserves the source values; `directional_metrics.friction` reverses its
sign so every positive directional delta means improvement. Comparison fails closed if either window
contains more rows than `--limit`; narrow the time range or raise the limit instead of comparing a
silent prefix.

```console
ucf --database assessments.db compare \
  --baseline-start 2026-08-01T00:00:00Z --baseline-end 2026-08-02T00:00:00Z \
  --candidate-start 2026-08-02T00:00:01Z --candidate-end 2026-08-03T00:00:00Z \
  --json
```

`check` applies thresholds to averages over the most recent bounded window. It exits 0 on pass and
5 on policy failure, making it suitable for CI without treating a failed threshold as malformed
input.

```console
ucf --database assessments.db check --limit 100 \
  --min-score 0.70 --min-harmony 0.65 --max-friction 0.25 --json
```

At least one threshold is required. Available minimums are score, harmony, resilience, throughput,
focus, and velocity; friction is a maximum because lower values are better.

## `ucf/v1` JSON object

```json
{
  "schema_version": "ucf/v1",
  "event_id": "release-check-1",
  "timestamp": "2026-07-28T01:02:03.000456Z",
  "phase": "HARMONIOUS",
  "score": 0.7183333333333334,
  "metrics": {
    "harmony": 0.65,
    "resilience": 0.72,
    "throughput": 0.7,
    "focus": 0.8,
    "friction": 0.18,
    "velocity": 0.62
  },
  "context": "pre-release review",
  "agent": "operator",
  "metadata": {}
}
```

The timestamp must include a UTC offset and is normalized to UTC. Unknown top-level fields and metric
fields other than the documented legacy aliases are rejected. Input requires `schema_version`,
`event_id`, `timestamp`, and `metrics`. `phase` and
`score` are optional derived cross-checks; `context`, `agent`, and `metadata` default when omitted.
Normalized output includes every field. The packaged schema is at
`ucf_protocol/schemas/ucf-state-v1.schema.json`; executable validation additionally enforces metadata
byte size/depth and agreement of derived fields. The schema defines the canonical exchange shape. The
Python parser additionally accepts the legacy metric aliases `prana`, `drishti`, `klesha`, and `zoom`
at its compatibility boundary and normalizes them to canonical names; alias-bearing input is therefore
parser-compatible but not schema-conformant.

## Python API

The stable public imports are exposed from `ucf_protocol`:

- `MetricSet`: immutable validated six-metric value object; `score`, `phase`, and `to_dict()`.
- `UCFState`: immutable observation; `to_dict()`, `to_json()`, and `from_dict()`.
- `UCFJournal`: SQLite persistence; `record`, `get`, `latest`, `recent`, `between`, `count`,
  `iter_all`, `record_many`, and `summary`.
- `ImportResult`: processed, would-be/actual recorded, skipped, and dry-run counts.
- `summarize_states()` and `compare_states()`: deterministic collection averages and transparent
  candidate-minus-baseline deltas.
- `QualityPolicy`, `evaluate_policy()`, and `GateResult`: explicit average-value CI gates.
- `state_from_json()` and `parse_timestamp()`: strict boundary parsers.
- `UCFValidationError`, `JournalError`, and `DuplicateEventError`: public failure types.
- `UCFProtocol`: compatibility formatting facade for callers of the earlier single-module API.

`UCFJournal` is a context manager. File-backed operations use short-lived connections and a busy
timeout; a `:memory:` journal retains one connection until `close()`.

```python
from datetime import datetime, timezone

from ucf_protocol import MetricSet, UCFJournal, UCFState

state = UCFState(
    metrics=MetricSet(0.65, 0.72, 0.70, 0.80, 0.18, 0.62),
    event_id="release-check-1",
    timestamp=datetime.now(timezone.utc),
    metadata={"source": "manual-rubric"},
)

with UCFJournal("journal.db") as journal:
    journal.record(state)
    recent = journal.recent(limit=20)
```

Metadata is recursively copied and frozen at construction, then thawed into ordinary JSON values on
serialization. Mutating the caller's original mapping cannot change a recorded `UCFState`.

## External correlation metadata

UCF does not own trace or experiment identifiers. Producers should place applicable identifiers in
the `metadata.correlation` object using these keys:

| Key | Meaning |
| --- | --- |
| `trace_id` | OpenTelemetry or platform trace identifier |
| `span_id` | Span or observation identifier |
| `session_id` | Conversation, workflow, or evaluation session |
| `experiment_id` | Dataset run or experiment identifier |
| `release_id` | Build, deployment, prompt, model, or release candidate |
| `evaluator_id` | Human, rubric, code evaluator, or model configuration |

Values are strings owned by the external system. Additional vendor-specific keys may be nested
under `metadata.vendor`; secrets, prompts, personal data, and authentication tokens should not be
copied into correlation metadata.

## Packaged conformance fixtures

The installed package includes `ucf_protocol/fixtures/manifest.json` plus valid, invalid, boundary,
and compatibility examples. Consumers can load them with `importlib.resources` and independently
verify both `expect` (the executable parser) and `schema_expect` (the canonical Draft 2020-12 schema).
The fixtures exercise minimal input, external correlation metadata, metric endpoints, legacy aliases,
invalid text, a missing required metric, and a derived-phase mismatch that only executable validation
can detect.
