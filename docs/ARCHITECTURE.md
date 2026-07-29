# Architecture

UCF Protocol is deliberately a single-process, local-first component:

```text
CLI or Python caller
        |
        v
strict ucf/v1 model ---- packaged JSON Schema
        |
        v
SQLite journal -------- JSON / JSONL export
```

## Components

`model.py` is the authority for metric validation, phase and score derivation, timestamps, event IDs,
bounded metadata, immutable observations, and JSON parsing. All external data crosses this boundary
before persistence.

`journal.py` owns schema version 1 of the SQLite journal. It uses parameterized statements, database
range checks, a primary key for idempotency, write-ahead logging for file databases, a busy timeout,
and bounded read methods. Rows are revalidated when read so corrupted or manually edited data fails
closed instead of silently entering the application.

`cli.py` maps operator input to the same model and journal APIs. It gives validation, duplicate,
empty-state, storage, and interruption failures distinct exit behavior. File export uses a temporary
file and `os.replace` to avoid publishing a partial result.

The JSON Schema is a portable structural contract. Python validation is intentionally stricter where
JSON Schema alone cannot express the derived score/phase relationship or total encoded metadata size.

## Trust boundaries

The process trusts the invoking operating-system account to choose its database and export paths. It
does not trust CLI strings, environment-provided paths, input files, stdin JSON, metadata, or existing
database contents. Those boundaries receive validation, bounds, parameter binding, or revalidation.

The product opens no listener, makes no network request, loads no plug-in code, and collects no
telemetry. Authentication and transport security are therefore outside the supported architecture.

## Data and concurrency

An observation is an append-only logical event identified by `event_id`; there is no update or delete
API. Multiple threads or local processes can write through independent connections. SQLite serializes
writes and UCF waits up to the configured busy timeout. This does not make the journal a distributed
database: do not put it on an unreliable network filesystem or share it between hosts.

The journal is not encrypted or authenticated. File permissions, disk encryption, backup, retention,
and secure deletion belong to the operator. Avoid placing secrets or regulated data in free-form
metadata.

## Versioning

`schema_version="ucf/v1"` versions the exchange format. SQLite `PRAGMA user_version=1` versions local
storage. An unknown storage version is rejected; there is no implicit downgrade. Breaking exchange
changes require a new schema identifier and migration plan.

## Intentionally absent

There is no hosted API, dashboard, Redis/PostgreSQL layer, OAuth, WebSocket stream, autonomous agent,
machine-learning model, or cloud deployment in this repository. Integrations can consume JSON/JSONL
or the Python API without expanding the trusted core.
