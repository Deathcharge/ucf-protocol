from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import pytest

from ucf_protocol import (
    MetricSet,
    UCFProtocol,
    UCFState,
    UCFValidationError,
    parse_timestamp,
    phase_for_harmony,
    state_from_json,
)
from ucf_protocol.model import PHASES

UTC = timezone.utc


def metrics(**overrides: float) -> MetricSet:
    values = {
        "harmony": 0.65,
        "resilience": 0.70,
        "throughput": 0.75,
        "focus": 0.80,
        "friction": 0.15,
        "velocity": 0.60,
    }
    values.update(overrides)
    return MetricSet(**values)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "CRITICAL"),
        (0.2999, "CRITICAL"),
        (0.3, "UNSTABLE"),
        (0.45, "COHERENT"),
        (0.6, "HARMONIOUS"),
        (0.8, "TRANSCENDENT"),
        (1.0, "TRANSCENDENT"),
    ],
)
def test_phase_boundaries(value: float, expected: str) -> None:
    assert phase_for_harmony(value) == expected
    assert UCFProtocol.get_phase(value) == expected


def test_compatibility_phase_ranges_derive_from_protocol_boundaries() -> None:
    assert list(UCFProtocol.PHASES) == [name for _, name in PHASES]
    assert UCFProtocol.PHASES["CRITICAL"] == (0.0, 0.3)
    assert UCFProtocol.PHASES["TRANSCENDENT"] == (0.8, 1.0)


@pytest.mark.parametrize("value", [-0.01, 1.01, math.inf, -math.inf, math.nan, True, "0.5"])
def test_metrics_reject_invalid_numbers(value: object) -> None:
    with pytest.raises(UCFValidationError):
        MetricSet(value, 0.5, 0.5, 0.5, 0.5, 0.5)  # type: ignore[arg-type]


def test_legacy_aliases_are_normalized_at_parse_boundary() -> None:
    parsed = MetricSet.from_mapping(
        {
            "harmony": 0.5,
            "resilience": 0.6,
            "prana": 0.7,
            "drishti": 0.8,
            "klesha": 0.2,
            "zoom": 0.9,
        }
    )
    assert parsed.to_dict() == {
        "harmony": 0.5,
        "resilience": 0.6,
        "throughput": 0.7,
        "focus": 0.8,
        "friction": 0.2,
        "velocity": 0.9,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "harmony": 0.5,
            "resilience": 0.5,
            "throughput": 0.5,
            "focus": 0.5,
            "friction": 0.5,
            "velocity": 0.5,
            "unknown": 0.5,
        },
        {
            "harmony": 0.5,
            "resilience": 0.5,
            "throughput": 0.5,
            "prana": 0.5,
            "focus": 0.5,
            "friction": 0.5,
            "velocity": 0.5,
        },
    ],
)
def test_metric_mapping_is_strict(payload: dict[str, float]) -> None:
    with pytest.raises(UCFValidationError):
        MetricSet.from_mapping(payload)


def test_metric_mapping_rejects_non_mapping_and_non_string_names() -> None:
    with pytest.raises(UCFValidationError, match="JSON object"):
        MetricSet.from_mapping([])  # type: ignore[arg-type]
    with pytest.raises(UCFValidationError, match="names"):
        MetricSet.from_mapping({1: 0.5})  # type: ignore[dict-item]


def test_score_is_equal_weight_and_inverts_friction() -> None:
    assert MetricSet(1, 1, 1, 1, 0, 1).score == 1.0
    assert MetricSet(0, 0, 0, 0, 1, 0).score == 0.0
    assert MetricSet(0.5, 0.5, 0.5, 0.5, 0.5, 0.5).score == 0.5


def test_state_round_trip_is_normalized_and_detached() -> None:
    state = UCFState(
        metrics=metrics(),
        event_id="deploy:42",
        timestamp=datetime(2026, 7, 28, 1, 2, 3, 456, tzinfo=UTC),
        context="release check",
        agent="operator",
        metadata={"tags": ["release", "local"], "attempt": 1},
    )
    payload = state.to_dict()
    assert payload["schema_version"] == "ucf/v1"
    assert payload["timestamp"] == "2026-07-28T01:02:03.000456Z"
    assert payload["phase"] == "HARMONIOUS"
    assert UCFState.from_dict(payload) == state
    assert state_from_json(state.to_json()) == state
    payload["metadata"]["attempt"] = 2
    assert state.to_dict()["metadata"]["attempt"] == 1
    with pytest.raises(TypeError):
        state.metadata["new"] = True  # type: ignore[index]


def test_state_rejects_derived_field_tampering() -> None:
    payload = UCFState(metrics=metrics(), event_id="event-1").to_dict()
    payload["phase"] = "CRITICAL"
    with pytest.raises(UCFValidationError, match="phase"):
        UCFState.from_dict(payload)

    payload = UCFState(metrics=metrics(), event_id="event-2").to_dict()
    payload["score"] = 0.0
    with pytest.raises(UCFValidationError, match="score"):
        UCFState.from_dict(payload)


@pytest.mark.parametrize("event_id", ["", " bad", "bad/id", "x" * 129])
def test_state_rejects_invalid_event_ids(event_id: str) -> None:
    with pytest.raises(UCFValidationError, match="event_id"):
        UCFState(metrics=metrics(), event_id=event_id)


def test_state_rejects_invalid_text_and_metadata() -> None:
    with pytest.raises(UCFValidationError, match="MetricSet"):
        UCFState(metrics={})  # type: ignore[arg-type]
    with pytest.raises(UCFValidationError, match="timestamp"):
        UCFState(metrics=metrics(), timestamp="now")  # type: ignore[arg-type]
    with pytest.raises(UCFValidationError, match="context"):
        UCFState(metrics=metrics(), context=" ")
    with pytest.raises(UCFValidationError, match="null"):
        UCFState(metrics=metrics(), context="bad\x00value")
    with pytest.raises(UCFValidationError, match="agent"):
        UCFState(metrics=metrics(), agent="a" * 129)
    with pytest.raises(UCFValidationError, match="JSON object"):
        UCFState(metrics=metrics(), metadata=[])  # type: ignore[arg-type]
    with pytest.raises(UCFValidationError, match="finite"):
        UCFState(metrics=metrics(), metadata={"bad": math.nan})
    with pytest.raises(UCFValidationError, match="unsupported"):
        UCFState(metrics=metrics(), metadata={"bad": object()})
    with pytest.raises(UCFValidationError, match="16384"):
        UCFState(metrics=metrics(), metadata={"large": "x" * 17_000})


def test_state_rejects_metadata_cycles_and_excessive_depth() -> None:
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic
    with pytest.raises(UCFValidationError, match="cycles"):
        UCFState(metrics=metrics(), metadata=cyclic)

    nested: dict[str, object] = {}
    current = nested
    for _ in range(10):
        child: dict[str, object] = {}
        current["child"] = child
        current = child
    with pytest.raises(UCFValidationError, match="nesting"):
        UCFState(metrics=metrics(), metadata=nested)

    with pytest.raises(UCFValidationError, match="objects"):
        UCFState(metrics=metrics(), metadata={str(index): index for index in range(257)})
    with pytest.raises(UCFValidationError, match="arrays"):
        UCFState(metrics=metrics(), metadata={"items": list(range(257))})
    with pytest.raises(UCFValidationError, match="keys"):
        UCFState(metrics=metrics(), metadata={1: "bad"})  # type: ignore[dict-item]


def test_timestamp_requires_valid_timezone() -> None:
    assert parse_timestamp("2026-07-27T21:00:00-04:00") == datetime(2026, 7, 28, 1, 0, tzinfo=UTC)
    with pytest.raises(UCFValidationError, match="offset"):
        parse_timestamp("2026-07-28T01:00:00")
    with pytest.raises(UCFValidationError, match="valid"):
        parse_timestamp("not-a-date")
    with pytest.raises(UCFValidationError, match="non-empty"):
        parse_timestamp(None)
    with pytest.raises(UCFValidationError, match="offset"):
        UCFState(metrics=metrics(), timestamp=datetime(2026, 7, 28))


def test_json_parser_reports_location_and_shape() -> None:
    with pytest.raises(UCFValidationError, match="line 1, column 2"):
        state_from_json("{")
    with pytest.raises(UCFValidationError, match="JSON object"):
        state_from_json("[]")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"unexpected": True}, "unknown state fields"),
        ({"schema_version": "ucf/v2"}, "schema_version"),
        ({"event_id": 42}, "event_id"),
        ({"metrics": []}, "metrics"),
        ({"context": 42}, "context"),
        ({"agent": 42}, "agent"),
        ({"metadata": []}, "metadata"),
    ],
)
def test_state_mapping_rejects_invalid_field_shapes(
    mutation: dict[str, object], message: str
) -> None:
    payload = UCFState(metrics=metrics(), event_id="event-1").to_dict()
    payload.update(mutation)
    with pytest.raises(UCFValidationError, match=message):
        UCFState.from_dict(payload)

    if "unexpected" in mutation:
        payload.pop("unexpected")


def test_state_mapping_requires_identity_timestamp_and_metrics() -> None:
    payload = UCFState(metrics=metrics(), event_id="event-1").to_dict()
    for required in ("event_id", "timestamp", "metrics"):
        incomplete = dict(payload)
        incomplete.pop(required)
        with pytest.raises(UCFValidationError, match="requires"):
            UCFState.from_dict(incomplete)


def test_state_mapping_accepts_optional_derived_and_descriptive_fields() -> None:
    payload = UCFState(metrics=metrics(), event_id="minimal-event").to_dict()
    minimal = {
        name: value
        for name, value in payload.items()
        if name in {"schema_version", "event_id", "timestamp", "metrics"}
    }
    parsed = UCFState.from_dict(minimal)
    assert parsed.event_id == "minimal-event"
    assert parsed.context is None
    assert parsed.agent is None
    assert parsed.metadata == {}


def test_compatibility_facade_formats_validated_values() -> None:
    compact = UCFProtocol.format_compact_state(0.65, 0.7, 0.75, 0.8, 0.15, 0.6)
    assert "HARMONIOUS" in compact
    assert "H=0.6500" in compact

    update = UCFProtocol.format_state_update(
        0.65, 0.7, 0.75, 0.8, 0.15, 0.6, context="check", agent="operator"
    )
    assert "Score:" in update
    assert "Context: check" in update
    assert "Agent: operator" in update

    message = UCFProtocol.format_agent_message("operator", "done", metrics().to_dict(), "success")
    assert message.startswith("[SUCCESS] [operator]")
    assert "UCF:" in message
    with pytest.raises(UCFValidationError, match="message_type"):
        UCFProtocol.format_agent_message("operator", "done", message_type="debug")
    for invalid_type in (None, 42, ""):
        with pytest.raises(UCFValidationError, match="message_type"):
            UCFProtocol.format_agent_message(
                "operator",
                "done",
                message_type=invalid_type,  # type: ignore[arg-type]
            )

    serialized = json.loads(UCFProtocol.to_json(0.65, 0.7, 0.75, 0.8, 0.15, 0.6))
    assert serialized["schema_version"] == "ucf/v1"

    minimal_update = UCFProtocol.format_state_update(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    assert "Context:" not in minimal_update
    assert "Agent:" not in minimal_update
    assert "UCF:" not in UCFProtocol.format_agent_message("operator", "done")
