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
| `validate` | Validate a complete `ucf/v1` JSON object | Does not open a journal |
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
| `130` | Interrupted by the user |

Argument parser errors use argparse's standard exit code 2.

### Bounds and safe defaults

- File/stdin observation input is limited to 65,536 UTF-8 bytes.
- Metadata is a JSON object limited to 16,384 encoded bytes, 256 items per collection, and eight
  nesting levels.
- Context is limited to 512 characters; agent labels to 128 characters.
- History and summary limits are integers from 1 through 1,000.
- Export does not overwrite an existing path without `--force`.
- SQL values use parameter binding. Event IDs are primary keys.

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

The timestamp must include a UTC offset and is normalized to UTC. Unknown top-level and metric fields
are rejected. `phase` and `score` are derived and verified during parsing. The packaged schema is at
`ucf_protocol/schemas/ucf-state-v1.schema.json`; executable validation additionally enforces metadata
byte size/depth and agreement of derived fields.

## Python API

The stable public imports are exposed from `ucf_protocol`:

- `MetricSet`: immutable validated six-metric value object; `score`, `phase`, and `to_dict()`.
- `UCFState`: immutable observation; `to_dict()`, `to_json()`, and `from_dict()`.
- `UCFJournal`: SQLite persistence; `record`, `get`, `latest`, `recent`, `between`, `count`,
  `iter_all`, and `summary`.
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
