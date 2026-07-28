"""Versioned UCF observation model and compatibility formatting helpers."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any
from uuid import uuid4

UTC = timezone.utc

SCHEMA_VERSION = "ucf/v1"
METRIC_NAMES = (
    "harmony",
    "resilience",
    "throughput",
    "focus",
    "friction",
    "velocity",
)
LEGACY_ALIASES = {
    "prana": "throughput",
    "drishti": "focus",
    "klesha": "friction",
    "zoom": "velocity",
}
PHASES = (
    (0.30, "CRITICAL"),
    (0.45, "UNSTABLE"),
    (0.60, "COHERENT"),
    (0.80, "HARMONIOUS"),
    (1.01, "TRANSCENDENT"),
)
TARGETS = {
    "harmony": 0.60,
    "resilience": 0.70,
    "throughput": 0.70,
    "focus": 0.70,
    "friction": 0.20,
    "velocity": 0.60,
}

_EVENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MAX_CONTEXT_LENGTH = 512
_MAX_AGENT_LENGTH = 128
_MAX_METADATA_BYTES = 16_384
_MAX_METADATA_DEPTH = 8
_MAX_METADATA_ITEMS = 256


class UCFValidationError(ValueError):
    """Raised when an observation violates the UCF protocol contract."""


def _metric_value(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UCFValidationError(f"{name} must be a number between 0 and 1")
    result = float(value)
    if not math.isfinite(result):
        raise UCFValidationError(f"{name} must be finite")
    if not 0.0 <= result <= 1.0:
        raise UCFValidationError(f"{name} must be between 0 and 1")
    return result


def phase_for_harmony(harmony: float) -> str:
    """Return the phase associated with a validated harmony value."""

    value = _metric_value("harmony", harmony)
    return next(phase for upper_bound, phase in PHASES if value < upper_bound)


def _validate_text(name: str, value: str | None, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise UCFValidationError(f"{name} must be a string")
    if not value.strip():
        raise UCFValidationError(f"{name} must not be blank")
    if len(value) > maximum:
        raise UCFValidationError(f"{name} must be at most {maximum} characters")
    if "\x00" in value:
        raise UCFValidationError(f"{name} must not contain a null character")
    return value


def _validate_metadata(value: object, *, depth: int = 0, seen: set[int] | None = None) -> None:
    if depth > _MAX_METADATA_DEPTH:
        raise UCFValidationError(f"metadata nesting must not exceed {_MAX_METADATA_DEPTH} levels")
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise UCFValidationError("metadata numbers must be finite")
        return

    if seen is None:
        seen = set()
    value_id = id(value)
    if value_id in seen:
        raise UCFValidationError("metadata must not contain cycles")

    if isinstance(value, Mapping):
        if len(value) > _MAX_METADATA_ITEMS:
            raise UCFValidationError(
                f"metadata objects must not contain more than {_MAX_METADATA_ITEMS} items"
            )
        seen.add(value_id)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise UCFValidationError("metadata object keys must be strings")
                _validate_metadata(item, depth=depth + 1, seen=seen)
        finally:
            seen.remove(value_id)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > _MAX_METADATA_ITEMS:
            raise UCFValidationError(
                f"metadata arrays must not contain more than {_MAX_METADATA_ITEMS} items"
            )
        seen.add(value_id)
        try:
            for item in value:
                _validate_metadata(item, depth=depth + 1, seen=seen)
        finally:
            seen.remove(value_id)
        return

    raise UCFValidationError(f"metadata contains unsupported value type {type(value).__name__}")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_thaw_json(item) for item in value]
    return value


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_timestamp(value: object) -> datetime:
    """Parse a timezone-aware ISO 8601 timestamp and normalize it to UTC."""

    if not isinstance(value, str) or not value:
        raise UCFValidationError("timestamp must be a non-empty ISO 8601 string")
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise UCFValidationError("timestamp must be a valid ISO 8601 value") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise UCFValidationError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class MetricSet:
    """The six finite, dimensionless UCF signals, each normalized to ``[0, 1]``."""

    harmony: float
    resilience: float
    throughput: float
    focus: float
    friction: float
    velocity: float

    def __post_init__(self) -> None:
        for name in METRIC_NAMES:
            object.__setattr__(self, name, _metric_value(name, getattr(self, name)))

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> MetricSet:
        if not isinstance(values, Mapping):
            raise UCFValidationError("metrics must be a JSON object")

        normalized: dict[str, object] = {}
        for supplied_name, value in values.items():
            if not isinstance(supplied_name, str):
                raise UCFValidationError("metric names must be strings")
            canonical_name = LEGACY_ALIASES.get(supplied_name, supplied_name)
            if canonical_name not in METRIC_NAMES:
                raise UCFValidationError(f"unknown metric: {supplied_name}")
            if canonical_name in normalized:
                raise UCFValidationError(f"metric supplied more than once: {canonical_name}")
            normalized[canonical_name] = value

        missing = [name for name in METRIC_NAMES if name not in normalized]
        if missing:
            raise UCFValidationError(f"missing metrics: {', '.join(missing)}")
        return cls(**normalized)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in METRIC_NAMES}

    @property
    def score(self) -> float:
        """Return the transparent equal-weight coordination score in ``[0, 1]``."""

        positive_total = (
            self.harmony
            + self.resilience
            + self.throughput
            + self.focus
            + self.velocity
            + (1.0 - self.friction)
        )
        return positive_total / 6.0

    @property
    def phase(self) -> str:
        return phase_for_harmony(self.harmony)


@dataclass(frozen=True, slots=True)
class UCFState:
    """One immutable point-in-time UCF observation."""

    metrics: MetricSet
    event_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: str | None = None
    agent: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.metrics, MetricSet):
            raise UCFValidationError("metrics must be a MetricSet")
        if not isinstance(self.event_id, str) or not _EVENT_ID_PATTERN.fullmatch(self.event_id):
            raise UCFValidationError(
                "event_id must start with an ASCII letter or digit and contain at most "
                "128 letters, digits, dots, underscores, colons, or hyphens"
            )
        if not isinstance(self.timestamp, datetime):
            raise UCFValidationError("timestamp must be a datetime")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise UCFValidationError("timestamp must include a UTC offset")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(
            self, "context", _validate_text("context", self.context, _MAX_CONTEXT_LENGTH)
        )
        object.__setattr__(self, "agent", _validate_text("agent", self.agent, _MAX_AGENT_LENGTH))

        if not isinstance(self.metadata, Mapping):
            raise UCFValidationError("metadata must be a JSON object")
        _validate_metadata(self.metadata)
        thawed = _thaw_json(self.metadata)
        try:
            encoded = json.dumps(
                thawed, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise UCFValidationError("metadata must be JSON serializable") from exc
        if len(encoded) > _MAX_METADATA_BYTES:
            raise UCFValidationError(
                f"metadata must be at most {_MAX_METADATA_BYTES} UTF-8 JSON bytes"
            )
        object.__setattr__(self, "metadata", _freeze_json(thawed))

    @property
    def phase(self) -> str:
        return self.metrics.phase

    @property
    def score(self) -> float:
        return self.metrics.score

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_id,
            "timestamp": _format_timestamp(self.timestamp),
            "phase": self.phase,
            "score": self.score,
            "metrics": self.metrics.to_dict(),
            "context": self.context,
            "agent": self.agent,
            "metadata": _thaw_json(self.metadata),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, allow_nan=False, indent=indent, sort_keys=True
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> UCFState:
        if not isinstance(payload, Mapping):
            raise UCFValidationError("state must be a JSON object")
        allowed = {
            "schema_version",
            "event_id",
            "timestamp",
            "phase",
            "score",
            "metrics",
            "context",
            "agent",
            "metadata",
        }
        unknown = sorted(str(key) for key in payload if key not in allowed)
        if unknown:
            raise UCFValidationError(f"unknown state fields: {', '.join(unknown)}")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise UCFValidationError(f"schema_version must be {SCHEMA_VERSION!r}")
        if "event_id" not in payload or "timestamp" not in payload or "metrics" not in payload:
            raise UCFValidationError("state requires event_id, timestamp, and metrics")
        raw_metrics = payload["metrics"]
        if not isinstance(raw_metrics, Mapping):
            raise UCFValidationError("metrics must be a JSON object")
        metrics = MetricSet.from_mapping(raw_metrics)

        expected_phase = metrics.phase
        if "phase" in payload and payload["phase"] != expected_phase:
            raise UCFValidationError(f"phase must be the derived value {expected_phase}")
        if "score" in payload:
            supplied_score = _metric_value("score", payload["score"])
            if not math.isclose(supplied_score, metrics.score, rel_tol=0.0, abs_tol=1e-12):
                raise UCFValidationError("score does not match the derived metric score")

        metadata = payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise UCFValidationError("metadata must be a JSON object")
        event_id = payload["event_id"]
        if not isinstance(event_id, str):
            raise UCFValidationError("event_id must be a string")
        context = payload.get("context")
        if context is not None and not isinstance(context, str):
            raise UCFValidationError("context must be a string")
        agent = payload.get("agent")
        if agent is not None and not isinstance(agent, str):
            raise UCFValidationError("agent must be a string")
        return cls(
            metrics=metrics,
            event_id=event_id,
            timestamp=parse_timestamp(payload["timestamp"]),
            context=context,
            agent=agent,
            metadata=metadata,
        )


class UCFProtocol:
    """Compatibility facade for formatting and serializing UCF observations."""

    PHASES = {
        "CRITICAL": (0.0, 0.30),
        "UNSTABLE": (0.30, 0.45),
        "COHERENT": (0.45, 0.60),
        "HARMONIOUS": (0.60, 0.80),
        "TRANSCENDENT": (0.80, 1.0),
    }
    TARGETS = MappingProxyType(TARGETS)

    @staticmethod
    def get_phase(harmony: float) -> str:
        return phase_for_harmony(harmony)

    @staticmethod
    def _metrics(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
    ) -> MetricSet:
        return MetricSet(harmony, resilience, throughput, focus, friction, velocity)

    @staticmethod
    def format_compact_state(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
    ) -> str:
        metrics = UCFProtocol._metrics(harmony, resilience, throughput, focus, friction, velocity)
        return (
            f"UCF: H={metrics.harmony:.4f} R={metrics.resilience:.4f} "
            f"T={metrics.throughput:.4f} F={metrics.focus:.4f} "
            f"X={metrics.friction:.4f} V={metrics.velocity:.4f} [{metrics.phase}]"
        )

    @staticmethod
    def format_state_update(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
        context: str | None = None,
        agent: str | None = None,
    ) -> str:
        state = UCFState(
            metrics=UCFProtocol._metrics(
                harmony, resilience, throughput, focus, friction, velocity
            ),
            context=context,
            agent=agent,
        )
        lines = [
            "UCF STATE UPDATE",
            f"Timestamp: {_format_timestamp(state.timestamp)}",
            f"Phase: {state.phase}",
            f"Score: {state.score:.4f}",
        ]
        if state.agent:
            lines.append(f"Agent: {state.agent}")
        if state.context:
            lines.append(f"Context: {state.context}")
        lines.extend(
            f"{name.capitalize()}: {value:.4f}" for name, value in state.metrics.to_dict().items()
        )
        return "\n".join(lines)

    @staticmethod
    def format_agent_message(
        agent_name: str,
        message: str,
        ucf_state: Mapping[str, object] | None = None,
        message_type: str = "INFO",
    ) -> str:
        agent = _validate_text("agent_name", agent_name, _MAX_AGENT_LENGTH)
        body = _validate_text("message", message, _MAX_CONTEXT_LENGTH)
        kind = message_type.upper()
        if kind not in {"INFO", "WARNING", "ERROR", "SUCCESS"}:
            raise UCFValidationError("message_type must be INFO, WARNING, ERROR, or SUCCESS")
        lines = [f"[{kind}] [{agent}] {_format_timestamp(datetime.now(UTC))}", str(body)]
        if ucf_state is not None:
            metrics = MetricSet.from_mapping(ucf_state)
            lines.append(UCFProtocol.format_compact_state(**metrics.to_dict()))
        return "\n".join(lines)

    @staticmethod
    def to_json(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        state = UCFState(
            metrics=UCFProtocol._metrics(
                harmony, resilience, throughput, focus, friction, velocity
            ),
            metadata=metadata or {},
        )
        return state.to_json()


def state_from_json(value: str) -> UCFState:
    """Parse and validate one JSON-encoded ``ucf/v1`` observation."""

    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise UCFValidationError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise UCFValidationError("state must be a JSON object")
    return UCFState.from_dict(payload)
