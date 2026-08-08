"""SQLite-backed persistence for UCF observations."""

from __future__ import annotations

import json
import math
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import METRIC_NAMES, UCFState, UCFValidationError, parse_timestamp

UTC = timezone.utc

_SCHEMA_VERSION = 1
_MAX_QUERY_LIMIT = 1_000
_EXPORT_BATCH_SIZE = 200


class JournalError(RuntimeError):
    """Raised when the local journal cannot complete an operation safely."""


class DuplicateEventError(JournalError):
    """Raised when an event ID already exists in the journal."""


def default_database_path() -> Path:
    """Return the platform-appropriate default local journal path."""

    configured = os.getenv("UCF_DATABASE")
    if configured:
        return Path(configured).expanduser()

    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ucf-protocol" / "journal.db"

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "ucf-protocol" / "journal.db"
    return Path.home() / ".local" / "share" / "ucf-protocol" / "journal.db"


def _limit(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise UCFValidationError("limit must be an integer")
    if not 1 <= value <= _MAX_QUERY_LIMIT:
        raise UCFValidationError(f"limit must be between 1 and {_MAX_QUERY_LIMIT}")
    return value


class UCFJournal:
    """A local, bounded-query journal with one SQLite connection per operation."""

    def __init__(self, path: str | os.PathLike[str] | None = None, *, timeout: float = 5.0):
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or not 0 < timeout <= 60
        ):
            raise UCFValidationError("timeout must be a finite number between 0 and 60 seconds")
        self.path = Path(path).expanduser() if path is not None else default_database_path()
        self.timeout = float(timeout)
        self._memory_connection: sqlite3.Connection | None = None
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _configure(self, connection: sqlite3.Connection) -> sqlite3.Connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")
        if str(self.path) != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if str(self.path) == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = self._configure(
                    sqlite3.connect(":memory:", timeout=self.timeout)
                )
            yield self._memory_connection
            return

        connection = self._configure(sqlite3.connect(self.path, timeout=self.timeout))
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        try:
            with self._connection() as connection:
                current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
                if current_version not in {0, _SCHEMA_VERSION}:
                    raise JournalError(
                        f"journal schema version {current_version} is not supported; "
                        f"expected {_SCHEMA_VERSION}"
                    )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS observations (
                        event_id TEXT PRIMARY KEY,
                        observed_at TEXT NOT NULL,
                        harmony REAL NOT NULL CHECK (harmony BETWEEN 0.0 AND 1.0),
                        resilience REAL NOT NULL CHECK (resilience BETWEEN 0.0 AND 1.0),
                        throughput REAL NOT NULL CHECK (throughput BETWEEN 0.0 AND 1.0),
                        focus REAL NOT NULL CHECK (focus BETWEEN 0.0 AND 1.0),
                        friction REAL NOT NULL CHECK (friction BETWEEN 0.0 AND 1.0),
                        velocity REAL NOT NULL CHECK (velocity BETWEEN 0.0 AND 1.0),
                        score REAL NOT NULL CHECK (score BETWEEN 0.0 AND 1.0),
                        phase TEXT NOT NULL CHECK (
                            phase IN (
                                'CRITICAL', 'UNSTABLE', 'COHERENT',
                                'HARMONIOUS', 'TRANSCENDENT'
                            )
                        ),
                        context TEXT,
                        agent TEXT,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_observations_observed_at
                    ON observations(observed_at DESC)
                    """
                )
                connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
                connection.commit()
        except JournalError:
            raise
        except sqlite3.Error as exc:
            raise JournalError(f"could not initialize journal at {self.path}: {exc}") from exc

    def record(self, state: UCFState) -> UCFState:
        if not isinstance(state, UCFState):
            raise UCFValidationError("state must be a UCFState")
        payload = state.to_dict()
        metrics = state.metrics.to_dict()
        try:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO observations (
                        event_id, observed_at, harmony, resilience, throughput,
                        focus, friction, velocity, score, phase, context, agent,
                        metadata_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state.event_id,
                        payload["timestamp"],
                        metrics["harmony"],
                        metrics["resilience"],
                        metrics["throughput"],
                        metrics["focus"],
                        metrics["friction"],
                        metrics["velocity"],
                        state.score,
                        state.phase,
                        state.context,
                        state.agent,
                        json.dumps(
                            payload["metadata"],
                            ensure_ascii=False,
                            allow_nan=False,
                            separators=(",", ":"),
                        ),
                        datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            if self.get(state.event_id) is not None:
                raise DuplicateEventError(f"event_id already exists: {state.event_id}") from exc
            raise JournalError(f"observation violated the journal schema: {exc}") from exc
        except sqlite3.Error as exc:
            raise JournalError(f"could not record observation in {self.path}: {exc}") from exc
        return state

    def get(self, event_id: str) -> UCFState | None:
        try:
            with self._connection() as connection:
                row = connection.execute(
                    "SELECT * FROM observations WHERE event_id = ?", (event_id,)
                ).fetchone()
        except sqlite3.Error as exc:
            raise JournalError(f"could not read journal at {self.path}: {exc}") from exc
        return self._row_to_state(row) if row is not None else None

    def latest(self) -> UCFState | None:
        try:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT * FROM observations
                    ORDER BY observed_at DESC, rowid DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error as exc:
            raise JournalError(f"could not read journal at {self.path}: {exc}") from exc
        return self._row_to_state(row) if row is not None else None

    def recent(self, *, limit: int = 20) -> list[UCFState]:
        safe_limit = _limit(limit)
        try:
            with self._connection() as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM observations
                    ORDER BY observed_at DESC, rowid DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise JournalError(f"could not read journal at {self.path}: {exc}") from exc
        return [self._row_to_state(row) for row in rows]

    def between(
        self, start: datetime, end: datetime, *, limit: int = _MAX_QUERY_LIMIT
    ) -> list[UCFState]:
        if not isinstance(start, datetime):
            raise UCFValidationError("start must be a datetime")
        if not isinstance(end, datetime):
            raise UCFValidationError("end must be a datetime")
        if start.tzinfo is None or start.utcoffset() is None:
            raise UCFValidationError("start must include a UTC offset")
        if end.tzinfo is None or end.utcoffset() is None:
            raise UCFValidationError("end must include a UTC offset")
        if start > end:
            raise UCFValidationError("start must not be after end")
        safe_limit = _limit(limit)
        start_text = start.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        end_text = end.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        try:
            with self._connection() as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM observations
                    WHERE observed_at BETWEEN ? AND ?
                    ORDER BY observed_at ASC, rowid ASC
                    LIMIT ?
                    """,
                    (start_text, end_text, safe_limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise JournalError(f"could not read journal at {self.path}: {exc}") from exc
        return [self._row_to_state(row) for row in rows]

    def count(self) -> int:
        try:
            with self._connection() as connection:
                row = connection.execute("SELECT COUNT(*) FROM observations").fetchone()
        except sqlite3.Error as exc:
            raise JournalError(f"could not read journal at {self.path}: {exc}") from exc
        return int(row[0])

    def iter_all(self) -> Iterator[UCFState]:
        last_observed_at: str | None = None
        last_rowid = 0
        while True:
            try:
                with self._connection() as connection:
                    if last_observed_at is None:
                        rows = connection.execute(
                            """
                            SELECT rowid AS export_rowid, * FROM observations
                            ORDER BY observed_at ASC, rowid ASC
                            LIMIT ?
                            """,
                            (_EXPORT_BATCH_SIZE,),
                        ).fetchall()
                    else:
                        rows = connection.execute(
                            """
                            SELECT rowid AS export_rowid, * FROM observations
                            WHERE observed_at > ? OR (observed_at = ? AND rowid > ?)
                            ORDER BY observed_at ASC, rowid ASC
                            LIMIT ?
                            """,
                            (
                                last_observed_at,
                                last_observed_at,
                                last_rowid,
                                _EXPORT_BATCH_SIZE,
                            ),
                        ).fetchall()
                    batch = [
                        (int(row["export_rowid"]), str(row["observed_at"]), self._row_to_state(row))
                        for row in rows
                    ]
            except sqlite3.Error as exc:
                raise JournalError(f"could not export journal at {self.path}: {exc}") from exc
            if not batch:
                return
            for _, _, state in batch:
                yield state
            last_rowid, last_observed_at, _ = batch[-1]

    def summary(self, *, limit: int = 100) -> dict[str, Any]:
        observations = list(reversed(self.recent(limit=limit)))
        if not observations:
            return {"count": 0, "metrics": {}, "score": {}, "harmony_delta": None}

        metric_summary: dict[str, dict[str, float]] = {}
        for name in METRIC_NAMES:
            values = [getattr(state.metrics, name) for state in observations]
            metric_summary[name] = {
                "average": sum(values) / len(values),
                "minimum": min(values),
                "maximum": max(values),
                "latest": values[-1],
            }
        scores = [state.score for state in observations]
        return {
            "count": len(observations),
            "metrics": metric_summary,
            "score": {
                "average": sum(scores) / len(scores),
                "minimum": min(scores),
                "maximum": max(scores),
                "latest": scores[-1],
            },
            "harmony_delta": observations[-1].metrics.harmony - observations[0].metrics.harmony,
        }

    def close(self) -> None:
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None

    def __enter__(self) -> UCFJournal:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> UCFState:
        try:
            metadata = json.loads(str(row["metadata_json"]))
        except (json.JSONDecodeError, TypeError) as exc:
            raise JournalError(f"stored metadata for event {row['event_id']} is invalid") from exc
        payload = {
            "schema_version": "ucf/v1",
            "event_id": row["event_id"],
            "timestamp": row["observed_at"],
            "phase": row["phase"],
            "score": row["score"],
            "metrics": {name: row[name] for name in METRIC_NAMES},
            "context": row["context"],
            "agent": row["agent"],
            "metadata": metadata,
        }
        try:
            return UCFState.from_dict(payload)
        except UCFValidationError as exc:
            raise JournalError(f"stored event {row['event_id']} violates ucf/v1: {exc}") from exc


def parse_range_timestamp(value: str) -> datetime:
    """Public helper used by the CLI for range arguments."""

    return parse_timestamp(value)
