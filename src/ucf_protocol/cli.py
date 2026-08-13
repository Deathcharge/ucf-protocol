"""Command-line interface for the local UCF journal."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from ._version import __version__
from .analysis import QualityPolicy, compare_states, evaluate_policy
from .journal import DuplicateEventError, JournalError, UCFJournal, default_database_path
from .model import (
    METRIC_NAMES,
    MetricSet,
    UCFState,
    UCFValidationError,
    parse_timestamp,
    state_from_json,
)

EXIT_ERROR = 1
EXIT_INVALID = 2
EXIT_EMPTY = 3
EXIT_DUPLICATE = 4
EXIT_GATE_FAILED = 5
_MAX_INPUT_BYTES = 65_536
_MAX_IMPORT_BYTES = 10 * 1024 * 1024
_MAX_IMPORT_ROWS = 10_000


def _bounded_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if not 1 <= parsed <= 1_000:
        raise argparse.ArgumentTypeError("must be between 1 and 1000")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ucf",
        description="Record and inspect local ucf/v1 coordination-health observations.",
    )
    parser.add_argument(
        "--database",
        metavar="PATH",
        help="SQLite journal path (default: UCF_DATABASE or the platform data directory)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize a journal and report its location")

    record = subparsers.add_parser("record", help="Validate and record one observation")
    record.add_argument(
        "--input",
        metavar="PATH",
        help="Read a complete ucf/v1 JSON object from PATH, or '-' for stdin",
    )
    for metric in METRIC_NAMES:
        record.add_argument(f"--{metric}", type=float, help=f"{metric} value in [0, 1]")
    record.add_argument("--event-id", help="Stable idempotency key (generated when omitted)")
    record.add_argument("--context", help="Optional bounded description of the observation")
    record.add_argument("--agent", help="Optional actor or source label")
    record.add_argument("--metadata", help="Optional JSON object, limited to 16 KiB")
    record.add_argument("--json", action="store_true", help="Print the stored observation as JSON")

    status = subparsers.add_parser("status", help="Show the latest observation")
    status.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    history = subparsers.add_parser("history", help="List recent observations")
    history.add_argument("--limit", type=_bounded_limit, default=20, help="Rows to show (1-1000)")
    history.add_argument("--json", action="store_true", help="Print a JSON array")

    summary = subparsers.add_parser("summary", help="Summarize a bounded recent window")
    summary.add_argument(
        "--limit", type=_bounded_limit, default=100, help="Rows to summarize (1-1000)"
    )
    summary.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    compare = subparsers.add_parser("compare", help="Compare two explicit observation windows")
    for prefix in ("baseline", "candidate"):
        compare.add_argument(f"--{prefix}-start", required=True, metavar="TIMESTAMP")
        compare.add_argument(f"--{prefix}-end", required=True, metavar="TIMESTAMP")
    compare.add_argument(
        "--limit", type=_bounded_limit, default=1000, help="Rows per window (1-1000)"
    )
    compare.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    check = subparsers.add_parser("check", help="Apply explicit thresholds to recent observations")
    check.add_argument("--limit", type=_bounded_limit, default=100, help="Rows to check (1-1000)")
    for metric in ("score", "harmony", "resilience", "throughput", "focus", "velocity"):
        check.add_argument(f"--min-{metric}", type=float)
    check.add_argument("--max-friction", type=float)
    check.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    validate = subparsers.add_parser("validate", help="Validate one ucf/v1 JSON object")
    validate.add_argument("path", metavar="PATH", help="JSON file path, or '-' for stdin")
    validate.add_argument("--json", action="store_true", help="Print normalized JSON")

    import_command = subparsers.add_parser("import", help="Atomically import ucf/v1 JSON Lines")
    import_command.add_argument("path", metavar="PATH", help="JSONL file path, or '-' for stdin")
    import_command.add_argument(
        "--on-duplicate",
        choices=("error", "skip"),
        default="error",
        help="Duplicate policy (default: error and roll back)",
    )
    import_command.add_argument(
        "--dry-run", action="store_true", help="Validate transaction without persisting rows"
    )
    import_command.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    export = subparsers.add_parser("export", help="Export the journal as JSON Lines")
    export.add_argument("--output", metavar="PATH", help="Destination file (default: stdout)")
    export.add_argument("--force", action="store_true", help="Replace an existing destination file")
    return parser


def _read_bounded(path: str, stdin: TextIO, *, maximum: int = _MAX_INPUT_BYTES) -> str:
    if path == "-":
        value = stdin.read(maximum + 1)
        source = "stdin"
    else:
        source_path = Path(path)
        try:
            with source_path.open("rb") as handle:
                raw = handle.read(maximum + 1)
        except OSError as exc:
            raise UCFValidationError(f"could not read {source_path}: {exc}") from exc
        if len(raw) > maximum:
            raise UCFValidationError(f"input must be at most {maximum} bytes")
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UCFValidationError(f"could not read {source_path}: {exc}") from exc
        source = str(source_path)
    if len(value.encode("utf-8")) > maximum:
        raise UCFValidationError(f"{source} input must be at most {maximum} bytes")
    return value


def _states_from_jsonl(path: str, stdin: TextIO) -> list[UCFState]:
    value = _read_bounded(path, stdin, maximum=_MAX_IMPORT_BYTES)
    states: list[UCFState] = []
    for line_number, raw_line in enumerate(value.split("\n"), start=1):
        line = raw_line.removesuffix("\r")
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > _MAX_INPUT_BYTES:
            raise UCFValidationError(
                f"JSONL line {line_number} must be at most {_MAX_INPUT_BYTES} bytes"
            )
        try:
            states.append(state_from_json(line))
        except UCFValidationError as exc:
            raise UCFValidationError(f"invalid JSONL line {line_number}: {exc}") from exc
        if len(states) > _MAX_IMPORT_ROWS:
            raise UCFValidationError(f"import must not exceed {_MAX_IMPORT_ROWS} observations")
    if not states:
        raise UCFValidationError("import requires at least one non-blank JSONL observation")
    return states


def _metadata(value: str | None) -> dict[str, Any]:
    if value is None:
        return {}
    if len(value.encode("utf-8")) > 16_384:
        raise UCFValidationError("metadata must be at most 16384 UTF-8 bytes")
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise UCFValidationError(f"invalid metadata JSON at column {exc.colno}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise UCFValidationError("metadata must be a JSON object")
    return payload


def _state_from_record_args(args: argparse.Namespace, stdin: TextIO) -> UCFState:
    supplied_metrics = {name: getattr(args, name) for name in METRIC_NAMES}
    if args.input:
        override_names = [
            *[name for name, value in supplied_metrics.items() if value is not None],
            *[
                name
                for name in ("event_id", "context", "agent", "metadata")
                if getattr(args, name) is not None
            ],
        ]
        if override_names:
            raise UCFValidationError(
                "--input cannot be combined with observation fields: " + ", ".join(override_names)
            )
        return state_from_json(_read_bounded(args.input, stdin))

    missing = [name for name, value in supplied_metrics.items() if value is None]
    if missing:
        raise UCFValidationError(
            "record requires --input or all six metrics; missing: " + ", ".join(missing)
        )
    metrics = MetricSet.from_mapping(supplied_metrics)
    state_kwargs: dict[str, Any] = {
        "metrics": metrics,
        "context": args.context,
        "agent": args.agent,
        "metadata": _metadata(args.metadata),
    }
    if args.event_id is not None:
        state_kwargs["event_id"] = args.event_id
    return UCFState(**state_kwargs)


def _print_state(state: UCFState, *, as_json: bool, stdout: TextIO) -> None:
    if as_json:
        print(state.to_json(), file=stdout)
        return
    print(f"Event: {state.event_id}", file=stdout)
    print(f"Timestamp: {state.to_dict()['timestamp']}", file=stdout)
    print(f"Phase: {state.phase}", file=stdout)
    print(f"Score: {state.score:.4f}", file=stdout)
    for name, value in state.metrics.to_dict().items():
        print(f"{name.capitalize()}: {value:.4f}", file=stdout)
    if state.agent:
        print(f"Agent: {state.agent}", file=stdout)
    if state.context:
        print(f"Context: {state.context}", file=stdout)


def _write_export(journal: UCFJournal, output: str | None, force: bool, stdout: TextIO) -> int:
    if output is None:
        count = 0
        for state in journal.iter_all():
            print(state.to_json(indent=None), file=stdout)
            count += 1
        return count

    destination = Path(output).expanduser()
    if destination.exists() and not force:
        raise UCFValidationError(f"destination exists; use --force to replace it: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            count = 0
            for state in journal.iter_all():
                handle.write(state.to_json(indent=None))
                handle.write("\n")
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists() and not force:
            raise UCFValidationError(f"destination appeared during export: {destination}")
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return count


def run(
    args: argparse.Namespace,
    *,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    if args.command == "validate":
        state = state_from_json(_read_bounded(args.path, stdin))
        if args.json:
            print(state.to_json(), file=stdout)
        else:
            print(
                f"Valid {state.to_dict()['schema_version']} observation: {state.event_id}",
                file=stdout,
            )
        return 0

    database = Path(args.database).expanduser() if args.database else default_database_path()
    if args.command == "import":
        states = _states_from_jsonl(args.path, stdin)
        journal_path: str | Path = (
            ":memory:" if args.dry_run and not database.exists() else database
        )
        with UCFJournal(journal_path) as journal:
            import_result = journal.record_many(
                states,
                on_duplicate=args.on_duplicate,
                dry_run=args.dry_run,
            )
        if args.json:
            print(json.dumps(import_result.to_dict(), indent=2, sort_keys=True), file=stdout)
        else:
            action = "Validated" if import_result.dry_run else "Imported"
            print(
                f"{action} {import_result.recorded} observations; "
                f"skipped {import_result.skipped} duplicates.",
                file=stdout,
            )
        return 0

    with UCFJournal(database) as journal:
        if args.command == "init":
            print(f"Journal ready: {journal.path} ({journal.count()} observations)", file=stdout)
            print("Next: ucf record --help", file=stdout)
            return 0

        if args.command == "record":
            state = _state_from_record_args(args, stdin)
            journal.record(state)
            if args.json:
                print(state.to_json(), file=stdout)
            else:
                print(
                    f"Recorded {state.event_id} ({state.phase}, score {state.score:.4f}).",
                    file=stdout,
                )
                print("Next: ucf status", file=stdout)
            return 0

        if args.command == "status":
            latest_state = journal.latest()
            if latest_state is None:
                raise EmptyJournalError(
                    "journal is empty; record an observation with `ucf record --help`"
                )
            _print_state(latest_state, as_json=args.json, stdout=stdout)
            return 0

        if args.command == "history":
            states = journal.recent(limit=args.limit)
            if args.json:
                print(
                    json.dumps(
                        [state.to_dict() for state in states],
                        ensure_ascii=False,
                        allow_nan=False,
                        indent=2,
                        sort_keys=True,
                    ),
                    file=stdout,
                )
            elif not states:
                print("Journal is empty. Next: ucf record --help", file=stdout)
            else:
                print(
                    "TIMESTAMP                    PHASE          SCORE   HARMONY  EVENT",
                    file=stdout,
                )
                for state in states:
                    print(
                        f"{state.to_dict()['timestamp']:<28} "
                        f"{state.phase:<14} {state.score:>6.4f}  "
                        f"{state.metrics.harmony:>7.4f}  {state.event_id}",
                        file=stdout,
                    )
            return 0

        if args.command == "summary":
            summary = journal.summary(limit=args.limit)
            if args.json:
                print(json.dumps(summary, indent=2, sort_keys=True), file=stdout)
            elif summary["count"] == 0:
                print("Journal is empty. Next: ucf record --help", file=stdout)
            else:
                print(f"Observations: {summary['count']}", file=stdout)
                print(f"Latest score: {summary['score']['latest']:.4f}", file=stdout)
                print(f"Average score: {summary['score']['average']:.4f}", file=stdout)
                print(f"Harmony delta: {summary['harmony_delta']:+.4f}", file=stdout)
            return 0

        if args.command == "compare":
            baseline = journal.between(
                parse_timestamp(args.baseline_start),
                parse_timestamp(args.baseline_end),
                limit=args.limit,
                reject_truncated=True,
            )
            candidate = journal.between(
                parse_timestamp(args.candidate_start),
                parse_timestamp(args.candidate_end),
                limit=args.limit,
                reject_truncated=True,
            )
            comparison = compare_states(baseline, candidate)
            if args.json:
                print(json.dumps(comparison, indent=2, sort_keys=True), file=stdout)
            else:
                print(
                    f"Baseline: {comparison['baseline']['count']} observations, "
                    f"score {comparison['baseline']['score']:.4f}",
                    file=stdout,
                )
                print(
                    f"Candidate: {comparison['candidate']['count']} observations, "
                    f"score {comparison['candidate']['score']:.4f}",
                    file=stdout,
                )
                print(f"Score delta: {comparison['delta']['score']:+.4f}", file=stdout)
                for name, delta in comparison["delta"]["directional_metrics"].items():
                    print(f"{name.capitalize()} improvement: {delta:+.4f}", file=stdout)
            return 0

        if args.command == "check":
            policy = QualityPolicy(
                min_score=args.min_score,
                min_harmony=args.min_harmony,
                min_resilience=args.min_resilience,
                min_throughput=args.min_throughput,
                min_focus=args.min_focus,
                max_friction=args.max_friction,
                min_velocity=args.min_velocity,
            )
            gate_result = evaluate_policy(journal.recent(limit=args.limit), policy)
            if args.json:
                print(json.dumps(gate_result.to_dict(), indent=2, sort_keys=True), file=stdout)
            elif gate_result.passed:
                print(
                    f"PASS: {gate_result.summary['count']} observations satisfy the policy.",
                    file=stdout,
                )
            else:
                print(f"FAIL: {len(gate_result.failures)} policy threshold(s) missed.", file=stdout)
                for failure in gate_result.failures:
                    print(f"- {failure}", file=stdout)
            return 0 if gate_result.passed else EXIT_GATE_FAILED

        if args.command == "export":
            count = _write_export(journal, args.output, args.force, stdout)
            if args.output:
                print(
                    f"Exported {count} observations to {Path(args.output).expanduser()}",
                    file=stdout,
                )
            return 0

    raise AssertionError(f"unhandled command: {args.command}")


class EmptyJournalError(RuntimeError):
    """Raised when a command requires an observation but the journal is empty."""


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return run(args, stdin=stdin, stdout=stdout)
    except EmptyJournalError as exc:
        print(f"error: {exc}", file=stderr)
        return EXIT_EMPTY
    except DuplicateEventError as exc:
        print(f"error: {exc}", file=stderr)
        return EXIT_DUPLICATE
    except (UCFValidationError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=stderr)
        return EXIT_INVALID
    except BrokenPipeError:
        return 0
    except (JournalError, OSError) as exc:
        print(f"error: {exc}", file=stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("error: interrupted", file=stderr)
        return 130


def entrypoint() -> None:
    """Console-script entry point."""

    raise SystemExit(main())
