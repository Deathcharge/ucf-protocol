from __future__ import annotations

import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from ucf_protocol import (
    DuplicateEventError,
    JournalError,
    MetricSet,
    UCFJournal,
    UCFState,
    UCFValidationError,
)
from ucf_protocol.journal import default_database_path, parse_range_timestamp
from ucf_protocol.model import PHASES

UTC = timezone.utc


def state(event_id: str, timestamp: datetime, harmony: float = 0.6) -> UCFState:
    return UCFState(
        metrics=MetricSet(harmony, 0.7, 0.7, 0.7, 0.2, 0.6),
        event_id=event_id,
        timestamp=timestamp,
        context="context '); DROP TABLE observations; --",
        metadata={"source": "test"},
    )


def test_empty_journal_initializes_and_persists(tmp_path) -> None:
    path = tmp_path / "nested" / "journal.db"
    with UCFJournal(path) as journal:
        assert path.exists()
        assert journal.count() == 0
        assert journal.latest() is None
        assert journal.recent() == []
        assert journal.summary() == {
            "count": 0,
            "metrics": {},
            "score": {},
            "harmony_delta": None,
        }


def test_record_read_order_and_duplicate_protection(tmp_path) -> None:
    path = tmp_path / "journal.db"
    start = datetime(2026, 7, 28, tzinfo=UTC)
    first = state("event-1", start, 0.5)
    second = state("event-2", start + timedelta(minutes=1), 0.7)
    with UCFJournal(path) as journal:
        assert journal.record(first) == first
        journal.record(second)
        assert journal.count() == 2
        assert journal.get("event-1") == first
        assert journal.get("missing") is None
        assert journal.latest() == second
        assert journal.recent(limit=2) == [second, first]
        with pytest.raises(DuplicateEventError, match="event-1"):
            journal.record(first)
        assert journal.count() == 2

    with UCFJournal(path) as reopened:
        assert reopened.latest() == second


def test_iter_all_preserves_order_across_bounded_batches(tmp_path) -> None:
    start = datetime(2026, 7, 28, tzinfo=UTC)
    with UCFJournal(tmp_path / "journal.db") as journal:
        for index in range(205):
            journal.record(state(f"event-{index:03}", start + timedelta(seconds=index)))
        assert [item.event_id for item in journal.iter_all()] == [
            f"event-{index:03}" for index in range(205)
        ]


def test_iter_all_closes_file_connection_before_first_yield(monkeypatch, tmp_path) -> None:
    path = tmp_path / "journal.db"
    with UCFJournal(path) as journal:
        journal.record(state("event-1", datetime(2026, 7, 28, tzinfo=UTC)))

        opened: list[sqlite3.Connection] = []
        connect = sqlite3.connect

        def tracked_connect(*args, **kwargs):
            connection = connect(*args, **kwargs)
            opened.append(connection)
            return connection

        monkeypatch.setattr(sqlite3, "connect", tracked_connect)
        iterator = journal.iter_all()
        assert next(iterator).event_id == "event-1"
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            opened[-1].execute("SELECT 1")


def test_between_and_summary_use_bounded_chronological_data(tmp_path) -> None:
    start = datetime(2026, 7, 28, tzinfo=UTC)
    with UCFJournal(tmp_path / "journal.db") as journal:
        for index, harmony in enumerate((0.4, 0.5, 0.8)):
            journal.record(state(f"event-{index}", start + timedelta(minutes=index), harmony))

        assert [item.event_id for item in journal.between(start, start + timedelta(minutes=1))] == [
            "event-0",
            "event-1",
        ]
        summary = journal.summary(limit=3)
        assert summary["count"] == 3
        assert summary["metrics"]["harmony"]["latest"] == 0.8
        assert summary["metrics"]["harmony"]["average"] == pytest.approx(1.7 / 3)
        assert summary["harmony_delta"] == pytest.approx(0.4)


@pytest.mark.parametrize("limit", [0, 1001, True, 1.5])
def test_query_limits_are_bounded(tmp_path, limit: object) -> None:
    with (
        UCFJournal(tmp_path / "journal.db") as journal,
        pytest.raises(UCFValidationError, match="limit"),
    ):
        journal.recent(limit=limit)  # type: ignore[arg-type]


def test_range_requires_aware_ordered_timestamps(tmp_path) -> None:
    with UCFJournal(tmp_path / "journal.db") as journal:
        aware = datetime(2026, 7, 28, tzinfo=UTC)
        with pytest.raises(UCFValidationError, match="start"):
            journal.between(datetime(2026, 7, 28), aware)
        with pytest.raises(UCFValidationError, match="end"):
            journal.between(aware, datetime(2026, 7, 28))
        with pytest.raises(UCFValidationError, match="after"):
            journal.between(aware + timedelta(seconds=1), aware)


def test_parameter_binding_preserves_sql_metacharacters(tmp_path) -> None:
    event = state("event-injection", datetime(2026, 7, 28, tzinfo=UTC))
    with UCFJournal(tmp_path / "journal.db") as journal:
        journal.record(event)
        assert journal.latest() == event
        assert journal.count() == 1


def test_concurrent_writers_use_independent_connections(tmp_path) -> None:
    path = tmp_path / "journal.db"
    start = datetime(2026, 7, 28, tzinfo=UTC)

    def write(index: int) -> None:
        with UCFJournal(path, timeout=10) as journal:
            journal.record(state(f"parallel-{index}", start + timedelta(seconds=index)))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(write, range(12)))

    with UCFJournal(path) as journal:
        assert journal.count() == 12


def test_memory_journal_retains_state_until_closed() -> None:
    journal = UCFJournal(":memory:")
    event = state("memory-event", datetime(2026, 7, 28, tzinfo=UTC))
    journal.record(event)
    assert journal.latest() == event
    journal.close()
    journal.initialize()
    assert journal.latest() is None
    journal.close()


def test_incompatible_schema_is_visible(tmp_path) -> None:
    path = tmp_path / "future.db"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA user_version = 99")
    connection.close()
    with pytest.raises(JournalError, match="not supported"):
        UCFJournal(path)


def test_journal_phase_constraint_matches_model(tmp_path) -> None:
    path = tmp_path / "journal.db"
    with UCFJournal(path):
        connection = sqlite3.connect(path)
        try:
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'observations'"
            ).fetchone()
        finally:
            connection.close()
    assert row is not None
    match = re.search(r"phase\s+IN\s*\((.*?)\)", str(row[0]), flags=re.IGNORECASE | re.DOTALL)
    assert match is not None
    assert re.findall(r"'([^']+)'", match.group(1)) == [name for _, name in PHASES]


def test_default_path_honors_explicit_environment(monkeypatch, tmp_path) -> None:
    configured = tmp_path / "configured.db"
    monkeypatch.setenv("UCF_DATABASE", str(configured))
    assert default_database_path() == configured


@pytest.mark.parametrize("timeout", [0, -1, 61, float("inf"), float("nan"), True, "5"])
def test_timeout_must_be_positive_number(timeout: object) -> None:
    with pytest.raises(UCFValidationError, match="timeout"):
        UCFJournal(":memory:", timeout=timeout)  # type: ignore[arg-type]


def test_record_requires_state_and_range_parser_is_public() -> None:
    with UCFJournal(":memory:") as journal, pytest.raises(UCFValidationError, match="UCFState"):
        journal.record({})  # type: ignore[arg-type]
    assert parse_range_timestamp("2026-07-28T00:00:00Z").tzinfo is not None


def test_range_requires_datetime_instances() -> None:
    with UCFJournal(":memory:") as journal:
        with pytest.raises(UCFValidationError, match="start"):
            journal.between("2026-07-28", datetime.now(UTC))  # type: ignore[arg-type]
        with pytest.raises(UCFValidationError, match="end"):
            journal.between(datetime.now(UTC), "2026-07-28")  # type: ignore[arg-type]


def test_corrupt_stored_rows_fail_closed(tmp_path) -> None:
    path = tmp_path / "corrupt.db"
    event = state("event-corrupt", datetime(2026, 7, 28, tzinfo=UTC))
    with UCFJournal(path) as journal:
        journal.record(event)

    connection = sqlite3.connect(path)
    connection.execute(
        "UPDATE observations SET metadata_json = '{' WHERE event_id = ?", (event.event_id,)
    )
    connection.commit()
    connection.close()
    with UCFJournal(path) as journal, pytest.raises(JournalError, match="metadata"):
        journal.latest()

    connection = sqlite3.connect(path)
    connection.execute(
        "UPDATE observations SET metadata_json = '{}', score = 0.0 WHERE event_id = ?",
        (event.event_id,),
    )
    connection.commit()
    connection.close()
    with UCFJournal(path) as journal, pytest.raises(JournalError, match="violates"):
        journal.latest()


@pytest.mark.parametrize("operation", ["get", "latest", "recent", "count", "iter_all"])
def test_read_operations_wrap_sqlite_errors(tmp_path, operation: str) -> None:
    path = tmp_path / f"broken-{operation}.db"
    journal = UCFJournal(path)
    connection = sqlite3.connect(path)
    connection.execute("DROP TABLE observations")
    connection.commit()
    connection.close()
    with pytest.raises(JournalError):
        result = (
            getattr(journal, operation)("id")
            if operation == "get"
            else getattr(journal, operation)()
        )
        if operation == "iter_all":
            list(result)


def test_record_wraps_missing_table_error(tmp_path) -> None:
    path = tmp_path / "broken-record.db"
    journal = UCFJournal(path)
    connection = sqlite3.connect(path)
    connection.execute("DROP TABLE observations")
    connection.commit()
    connection.close()
    with pytest.raises(JournalError, match="record"):
        journal.record(state("event-1", datetime(2026, 7, 28, tzinfo=UTC)))


def test_initialize_wraps_invalid_sqlite_file(tmp_path) -> None:
    path = tmp_path / "not-a-database.db"
    path.write_text("not sqlite", encoding="utf-8")
    with pytest.raises(JournalError, match="initialize"):
        UCFJournal(path)
