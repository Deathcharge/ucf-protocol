"""Portable, local-only score records for external evaluation adapters."""

from __future__ import annotations

from typing import Any

from .model import METRIC_NAMES, UCFState, UCFValidationError


def score_records(state: UCFState) -> list[dict[str, Any]]:
    """Project one observation into six independent, versioned numeric scores.

    Context, actor labels and arbitrary metadata are deliberately excluded. Only
    explicitly documented correlation identifiers cross this export boundary.
    """

    if not isinstance(state, UCFState):
        raise UCFValidationError("state must be a UCFState")
    payload = state.to_dict()
    raw = payload["metadata"].get("correlation", {})
    if not isinstance(raw, dict):
        raise UCFValidationError("metadata.correlation must be an object for score export")
    correlation = {}
    for key in ("trace_id", "span_id", "session_id", "experiment_id", "release_id", "evaluator_id"):
        if key in raw:
            value = raw[key]
            if not isinstance(value, str) or not value.strip():
                raise UCFValidationError(f"metadata.correlation.{key} must be a non-blank string")
            correlation[key] = value
    return [
        {
            "schema_version": "ucf/scores/v1",
            "id": f"{state.event_id}:{name}",
            "event_id": state.event_id,
            "timestamp": payload["timestamp"],
            "name": f"ucf.{name}",
            "value": getattr(state.metrics, name),
            "higher_is_better": name != "friction",
            "correlation": dict(correlation),
        }
        for name in METRIC_NAMES
    ]
