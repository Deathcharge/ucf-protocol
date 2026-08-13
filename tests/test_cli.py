from __future__ import annotations

import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

import ucf_protocol.cli as cli_module
from ucf_protocol.cli import EXIT_DUPLICATE, EXIT_EMPTY, EXIT_GATE_FAILED, EXIT_INVALID, main


def invoke(arguments: list[str], stdin: str = "") -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    result = main(arguments, stdin=StringIO(stdin), stdout=stdout, stderr=stderr)
    return result, stdout.getvalue(), stderr.getvalue()


def record_args(path: Path, event_id: str = "event-1") -> list[str]:
    return [
        "--database",
        str(path),
        "record",
        "--event-id",
        event_id,
        "--harmony",
        "0.65",
        "--resilience",
        "0.7",
        "--throughput",
        "0.75",
        "--focus",
        "0.8",
        "--friction",
        "0.15",
        "--velocity",
        "0.6",
        "--context",
        "release check",
        "--metadata",
        '{"source":"cli"}',
    ]


def test_init_and_empty_states_are_actionable(tmp_path) -> None:
    path = tmp_path / "journal.db"
    code, stdout, stderr = invoke(["--database", str(path), "init"])
    assert code == 0
    assert "Journal ready" in stdout
    assert "ucf record --help" in stdout
    assert stderr == ""

    code, stdout, stderr = invoke(["--database", str(path), "status"])
    assert code == EXIT_EMPTY
    assert stdout == ""
    assert "journal is empty" in stderr

    code, stdout, stderr = invoke(["--database", str(path), "history"])
    assert code == 0
    assert "Journal is empty" in stdout
    assert stderr == ""


def test_record_status_history_and_summary_journey(tmp_path) -> None:
    path = tmp_path / "journal.db"
    code, stdout, stderr = invoke(record_args(path))
    assert code == 0
    assert "Recorded event-1" in stdout
    assert "Next: ucf status" in stdout
    assert stderr == ""

    code, stdout, _ = invoke(["--database", str(path), "status", "--json"])
    payload = json.loads(stdout)
    assert code == 0
    assert payload["event_id"] == "event-1"
    assert payload["metadata"] == {"source": "cli"}

    code, stdout, _ = invoke(["--database", str(path), "history", "--limit", "1"])
    assert code == 0
    assert "HARMONIOUS" in stdout
    assert "event-1" in stdout

    code, stdout, _ = invoke(["--database", str(path), "summary", "--json"])
    summary = json.loads(stdout)
    assert code == 0
    assert summary["count"] == 1
    assert summary["metrics"]["harmony"]["latest"] == 0.65


def test_duplicate_and_invalid_inputs_have_distinct_exit_codes(tmp_path) -> None:
    path = tmp_path / "journal.db"
    assert invoke(record_args(path))[0] == 0
    code, _, stderr = invoke(record_args(path))
    assert code == EXIT_DUPLICATE
    assert "already exists" in stderr

    invalid = record_args(path, "event-2")
    invalid[invalid.index("0.65")] = "nan"
    code, _, stderr = invoke(invalid)
    assert code == EXIT_INVALID
    assert "finite" in stderr

    code, _, stderr = invoke(["--database", str(path), "record", "--harmony", "0.5"])
    assert code == EXIT_INVALID
    assert "missing" in stderr

    code, _, stderr = invoke(
        ["--database", str(path), "record", "--input", "-", "--agent", "override"],
        stdin="{}",
    )
    assert code == EXIT_INVALID
    assert "cannot be combined" in stderr


def test_validate_and_record_complete_json(tmp_path) -> None:
    path = tmp_path / "journal.db"
    assert invoke(record_args(path))[0] == 0
    _, state_json, _ = invoke(["--database", str(path), "status", "--json"])

    code, normalized, stderr = invoke(["validate", "-", "--json"], stdin=state_json)
    assert code == 0
    assert json.loads(normalized)["event_id"] == "event-1"
    assert stderr == ""

    other_path = tmp_path / "other.db"
    code, stdout, stderr = invoke(
        ["--database", str(other_path), "record", "--input", "-", "--json"],
        stdin=state_json,
    )
    assert code == 0
    assert json.loads(stdout)["event_id"] == "event-1"
    assert stderr == ""


def test_validate_rejects_oversized_and_malformed_input(tmp_path) -> None:
    too_large = tmp_path / "large.json"
    too_large.write_text("x" * 65_537, encoding="utf-8")
    code, _, stderr = invoke(["validate", str(too_large)])
    assert code == EXIT_INVALID
    assert "65536" in stderr

    code, _, stderr = invoke(["validate", "-"], stdin="{")
    assert code == EXIT_INVALID
    assert "invalid JSON" in stderr

    invalid_utf8 = tmp_path / "invalid-utf8.json"
    invalid_utf8.write_bytes(b"\xff")
    code, _, stderr = invoke(["validate", str(invalid_utf8)])
    assert code == EXIT_INVALID
    assert "could not read" in stderr


def test_export_is_jsonl_and_does_not_overwrite_without_force(tmp_path) -> None:
    path = tmp_path / "journal.db"
    assert invoke(record_args(path))[0] == 0

    code, stdout, stderr = invoke(["--database", str(path), "export"])
    assert code == 0
    assert json.loads(stdout)["event_id"] == "event-1"
    assert stderr == ""

    destination = tmp_path / "export.jsonl"
    destination.write_text("keep", encoding="utf-8")
    code, _, stderr = invoke(["--database", str(path), "export", "--output", str(destination)])
    assert code == EXIT_INVALID
    assert destination.read_text(encoding="utf-8") == "keep"
    assert "--force" in stderr

    code, stdout, stderr = invoke(
        ["--database", str(path), "export", "--output", str(destination), "--force"]
    )
    assert code == 0
    assert "Exported 1" in stdout
    assert json.loads(destination.read_text(encoding="utf-8"))["event_id"] == "event-1"
    assert stderr == ""


def test_jsonl_import_is_atomic_dry_runnable_and_duplicate_aware(tmp_path) -> None:
    source_path = tmp_path / "source.db"
    assert invoke(record_args(source_path, "one"))[0] == 0
    _, first_json, _ = invoke(["--database", str(source_path), "status", "--json"])
    second = json.loads(first_json)
    second["event_id"] = "two"
    second["timestamp"] = "2026-08-08T00:00:01Z"
    jsonl = json.dumps(json.loads(first_json)) + "\n\n" + json.dumps(second) + "\n"

    destination = tmp_path / "destination.db"
    code, output, stderr = invoke(
        ["--database", str(destination), "import", "-", "--dry-run", "--json"], stdin=jsonl
    )
    assert code == 0
    assert json.loads(output) == {
        "dry_run": True,
        "processed": 2,
        "recorded": 2,
        "skipped": 0,
    }
    assert stderr == ""
    assert not destination.exists()
    assert invoke(["--database", str(destination), "history", "--json"])[1].strip() == "[]"

    code, output, stderr = invoke(["--database", str(destination), "import", "-"], stdin=jsonl)
    assert code == 0
    assert "Imported 2" in output
    assert stderr == ""

    code, _, stderr = invoke(["--database", str(destination), "import", "-"], stdin=jsonl)
    assert code == EXIT_DUPLICATE
    assert "already exists" in stderr
    history = invoke(["--database", str(destination), "history", "--json"])[1]
    assert len(json.loads(history)) == 2

    code, output, stderr = invoke(
        ["--database", str(destination), "import", "-", "--on-duplicate", "skip", "--json"],
        stdin=jsonl,
    )
    assert code == 0
    assert json.loads(output)["skipped"] == 2
    assert stderr == ""


def test_jsonl_import_rejects_empty_bad_and_oversized_lines(tmp_path) -> None:
    path = tmp_path / "journal.db"
    code, _, stderr = invoke(["--database", str(path), "import", "-"], stdin="\n")
    assert code == EXIT_INVALID
    assert "at least one" in stderr
    assert not path.exists()

    code, _, stderr = invoke(["--database", str(path), "import", "-"], stdin='{}\n{"bad":')
    assert code == EXIT_INVALID
    assert "line 1" in stderr
    assert not path.exists()

    code, _, stderr = invoke(["--database", str(path), "import", "-"], stdin=" " * 65_537 + "x\n")
    assert code == EXIT_INVALID
    assert "line 1" in stderr
    assert not path.exists()


@pytest.mark.parametrize("separator", ("\u0085", "\u2028", "\u2029"))
def test_exported_jsonl_round_trips_unicode_separators(tmp_path: Path, separator: str) -> None:
    source = tmp_path / "source.db"
    arguments = record_args(source)
    arguments[arguments.index("release check")] = f"before{separator}after"
    arguments[arguments.index('{"source":"cli"}')] = json.dumps(
        {"separator": f"before{separator}after"}, ensure_ascii=False
    )
    assert invoke(arguments)[0] == 0

    code, exported, stderr = invoke(["--database", str(source), "export"])
    assert code == 0
    assert exported.count("\n") == 1
    assert stderr == ""

    destination = tmp_path / "destination.db"
    code, _, stderr = invoke(["--database", str(destination), "import", "-"], stdin=exported)
    assert code == 0
    assert stderr == ""
    _, imported, _ = invoke(["--database", str(destination), "status", "--json"])
    payload = json.loads(imported)
    assert payload["context"] == f"before{separator}after"
    assert payload["metadata"]["separator"] == f"before{separator}after"


def test_module_entrypoint_reports_version_from_outside_repo(tmp_path) -> None:
    source = Path(__file__).parents[1] / "src"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source)
    result = subprocess.run(
        [sys.executable, "-m", "ucf_protocol", "--version"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "ucf 1.0.0rc1"
    assert result.stderr == ""


def test_human_and_json_output_branches(tmp_path) -> None:
    path = tmp_path / "journal.db"
    json_args = record_args(path, "generated")
    json_args.extend(["--agent", "operator", "--json"])
    code, stdout, stderr = invoke(json_args)
    assert code == 0
    assert json.loads(stdout)["agent"] == "operator"
    assert stderr == ""

    code, stdout, _ = invoke(["--database", str(path), "status"])
    assert code == 0
    assert "Agent: operator" in stdout
    assert "Context: release check" in stdout

    code, stdout, _ = invoke(["--database", str(path), "history", "--json"])
    assert code == 0
    assert json.loads(stdout)[0]["event_id"] == "generated"

    code, stdout, _ = invoke(["--database", str(path), "summary"])
    assert code == 0
    assert "Observations: 1" in stdout


def test_empty_summary_and_human_validate(tmp_path) -> None:
    path = tmp_path / "journal.db"
    code, stdout, stderr = invoke(["--database", str(path), "summary"])
    assert code == 0
    assert "Journal is empty" in stdout
    assert stderr == ""

    state_path = tmp_path / "state.json"
    payload = {
        "schema_version": "ucf/v1",
        "event_id": "event-file",
        "timestamp": "2026-07-28T00:00:00Z",
        "phase": "HARMONIOUS",
        "score": 0.6166666666666667,
        "metrics": {
            "harmony": 0.6,
            "resilience": 0.6,
            "throughput": 0.6,
            "focus": 0.6,
            "friction": 0.3,
            "velocity": 0.6,
        },
        "context": None,
        "agent": None,
        "metadata": {},
    }
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    code, stdout, stderr = invoke(["validate", str(state_path)])
    assert code == 0
    assert "Valid ucf/v1 observation: event-file" in stdout
    assert stderr == ""


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ("{", "invalid metadata JSON"),
        ("[]", "JSON object"),
        (json.dumps({"value": "x" * 17_000}), "16384"),
    ],
)
def test_record_rejects_bad_metadata(tmp_path, metadata: str, message: str) -> None:
    arguments = record_args(tmp_path / "journal.db")
    metadata_index = arguments.index("--metadata") + 1
    arguments[metadata_index] = metadata
    code, _, stderr = invoke(arguments)
    assert code == EXIT_INVALID
    assert message in stderr


def test_missing_files_and_bad_database_are_clean_errors(tmp_path) -> None:
    code, _, stderr = invoke(["validate", str(tmp_path / "missing.json")])
    assert code == EXIT_INVALID
    assert "could not read" in stderr

    directory = tmp_path / "database-directory"
    directory.mkdir()
    code, _, stderr = invoke(["--database", str(directory), "init"])
    assert code == 1
    assert "initialize" in stderr


def test_interrupt_and_broken_pipe_are_stable_exit_codes(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module, "run", lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt)
    )
    code, _, stderr = invoke(["init"])
    assert code == 130
    assert "interrupted" in stderr

    monkeypatch.setattr(
        cli_module, "run", lambda *args, **kwargs: (_ for _ in ()).throw(BrokenPipeError)
    )
    assert invoke(["init"])[0] == 0


def test_entrypoint_converts_return_code_to_system_exit(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "main", lambda: 4)
    with pytest.raises(SystemExit) as exc_info:
        cli_module.entrypoint()
    assert exc_info.value.code == 4


def test_compare_and_policy_gate_commands(tmp_path) -> None:
    path = tmp_path / "journal.db"
    first = record_args(path, "baseline")
    first.extend(["--json"])
    assert invoke(first)[0] == 0

    code, comparison_json, stderr = invoke(
        [
            "--database",
            str(path),
            "compare",
            "--baseline-start",
            "2000-01-01T00:00:00Z",
            "--baseline-end",
            "2100-01-01T00:00:00Z",
            "--candidate-start",
            "2000-01-01T00:00:00Z",
            "--candidate-end",
            "2100-01-01T00:00:00Z",
            "--json",
        ]
    )
    assert code == 0
    assert json.loads(comparison_json)["delta"]["score"] == 0
    assert stderr == ""

    code, output, stderr = invoke(
        ["--database", str(path), "check", "--min-harmony", "0.6", "--max-friction", "0.2"]
    )
    assert code == 0
    assert output.startswith("PASS:")
    assert stderr == ""

    code, output, stderr = invoke(
        ["--database", str(path), "check", "--min-harmony", "0.9", "--json"]
    )
    assert code == EXIT_GATE_FAILED
    assert json.loads(output)["passed"] is False
    assert stderr == ""


def test_compare_and_gate_reject_empty_or_invalid_configuration(tmp_path) -> None:
    path = tmp_path / "journal.db"
    code, _, stderr = invoke(["--database", str(path), "check", "--min-score", "0.5"])
    assert code == EXIT_INVALID
    assert "at least one observation" in stderr

    code, _, stderr = invoke(["--database", str(path), "check"])
    assert code == EXIT_INVALID
    assert "threshold" in stderr


def test_compare_rejects_truncated_windows(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    assert invoke(record_args(path, "first"))[0] == 0
    assert invoke(record_args(path, "second"))[0] == 0
    code, _, stderr = invoke(
        [
            "--database",
            str(path),
            "compare",
            "--baseline-start",
            "2000-01-01T00:00:00Z",
            "--baseline-end",
            "2100-01-01T00:00:00Z",
            "--candidate-start",
            "2000-01-01T00:00:00Z",
            "--candidate-end",
            "2100-01-01T00:00:00Z",
            "--limit",
            "1",
        ]
    )
    assert code == EXIT_INVALID
    assert "more than 1 observations" in stderr
