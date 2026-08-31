"""Offline preview of UCF scores mapped to Langfuse create_score keyword arguments."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from ucf_protocol import UCFState, UCFValidationError, score_records, state_from_json


def langfuse_score_arguments(state: UCFState) -> list[dict[str, Any]]:
    """Prepare six score calls; never instantiate a client or transmit data."""

    rows = score_records(state)
    calls = []
    for row in rows:
        correlation = row["correlation"]
        if not correlation.get("trace_id") and not correlation.get("session_id"):
            raise UCFValidationError("Langfuse adapter requires trace_id or session_id")
        if correlation.get("span_id") and not correlation.get("trace_id"):
            raise UCFValidationError("span_id requires trace_id")
        arguments = {
            "score_id": row["id"],
            "name": row["name"],
            "value": row["value"],
            "data_type": "NUMERIC",
            "metadata": {
                "ucf_event_id": row["event_id"],
                "ucf_timestamp": row["timestamp"],
                "higher_is_better": row["higher_is_better"],
            },
        }
        for source, target in (
            ("trace_id", "trace_id"),
            ("span_id", "observation_id"),
            ("session_id", "session_id"),
        ):
            if source in correlation:
                arguments[target] = correlation[source]
        calls.append(arguments)
    return calls


def main() -> None:
    fixture = files("ucf_protocol").joinpath("fixtures/valid-correlated.json")
    state = state_from_json(fixture.read_text(encoding="utf-8"))
    print(json.dumps(langfuse_score_arguments(state), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
