from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from ucf_protocol import MetricSet, UCFState, UCFValidationError


def adapter():
    path = Path(__file__).parents[1] / "examples" / "langfuse_adapter.py"
    spec = importlib.util.spec_from_file_location("langfuse_example", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_adapter_preserves_score_ids_and_targets() -> None:
    state = UCFState(
        MetricSet(0.7, 0.7, 0.7, 0.7, 0.2, 0.7),
        event_id="review-1",
        metadata={"correlation": {"trace_id": "a" * 32, "span_id": "b" * 16}},
    )
    calls = adapter().langfuse_score_arguments(state)
    assert len(calls) == 6
    assert calls[0]["score_id"] == "review-1:harmony"
    assert all(call["trace_id"] == "a" * 32 for call in calls)
    assert all(call["observation_id"] == "b" * 16 for call in calls)
    assert calls[4]["value"] == 0.2
    assert calls[4]["metadata"]["higher_is_better"] is False


@pytest.mark.parametrize("correlation", [{}, {"session_id": "s", "span_id": "b" * 16}])
def test_adapter_rejects_unaddressable_scores(correlation) -> None:
    state = UCFState(MetricSet(0, 0, 0, 0, 0, 0), metadata={"correlation": correlation})
    with pytest.raises(UCFValidationError):
        adapter().langfuse_score_arguments(state)


def test_session_target_and_offline_preview(capsys) -> None:
    state = UCFState(MetricSet(0, 0, 0, 0, 0, 0), metadata={"correlation": {"session_id": "s"}})
    assert adapter().langfuse_score_arguments(state)[0]["session_id"] == "s"
    adapter().main()
    assert '"data_type": "NUMERIC"' in capsys.readouterr().out
