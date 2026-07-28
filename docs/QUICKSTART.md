# Quick start

This guide takes a new user from a checkout to a validated local observation. It requires Python
3.10 or newer and does not require network access after installation.

## 1. Install

```console
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install .
```

Confirm which release candidate you installed:

```console
ucf --version
ucf --help
```

## 2. Initialize a journal

Choose the database path explicitly when learning the tool:

```console
ucf --database quickstart.db init
```

The database contains only observations you record. `init` can be repeated safely.

## 3. Record one observation

```console
ucf --database quickstart.db record --event-id quickstart-1 --harmony 0.65 --resilience 0.72 --throughput 0.70 --focus 0.80 --friction 0.18 --velocity 0.62 --context "quick-start check" --agent "operator"
```

All six metrics are required and must be finite numbers from 0 through 1. An `event-id` is generated
when omitted; supplying one makes retries idempotent. Reusing an ID returns exit code 4 and does not
insert a second row.

## 4. Inspect the result

```console
ucf --database quickstart.db status
ucf --database quickstart.db history --limit 10
ucf --database quickstart.db summary
```

Append `--json` to `status`, `history`, or `summary` for machine-readable output.

## 5. Validate and import JSON

Export the latest observation as JSON, validate it, and record it in another journal:

```console
ucf --database quickstart.db status --json > observation.json
ucf validate observation.json
ucf --database copy.db record --input observation.json
```

Complete JSON observations must conform to `ucf/v1`. Derived `phase` and `score` values are checked,
not trusted.

## 6. Export history

```console
ucf --database quickstart.db export --output observations.jsonl
```

Existing files are not replaced unless `--force` is present. File export writes a temporary file,
flushes it, and atomically replaces the destination when the operating system supports the standard
same-filesystem rename guarantee.

## Default database location

Omitting `--database` uses `UCF_DATABASE` when set. Otherwise UCF uses the platform user-data
directory: `%LOCALAPPDATA%\ucf-protocol\journal.db` on Windows, or
`$XDG_DATA_HOME/ucf-protocol/journal.db` / `~/.local/share/ucf-protocol/journal.db` elsewhere.

For the exact contract, continue to [API.md](API.md) and [UCF_METRICS.md](../UCF_METRICS.md).
