from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ucf_protocol import (
    MetricSet,
    QualityPolicy,
    UCFState,
    UCFValidationError,
    compare_states,
    evaluate_policy,
    summarize_states,
)

UTC = timezone.utc


def observation(event_id: str, harmony: float, friction: float = 0.2) -> UCFState:
    return UCFState(
        metrics=MetricSet(harmony, 0.7, 0.6, 0.8, friction, 0.65),
        event_id=event_id,
        timestamp=datetime(2026, 8, 8, tzinfo=UTC),
    )


def test_summary_and_comparison_report_raw_and_directional_deltas() -> None:
    baseline = [observation("baseline", 0.5, 0.3)]
    candidate = [observation("candidate-1", 0.7, 0.1), observation("candidate-2", 0.9, 0.2)]

    summary = summarize_states(candidate)
    assert summary["count"] == 2
    assert summary["metrics"]["harmony"] == pytest.approx(0.8)

    comparison = compare_states(baseline, candidate)
    assert comparison["delta"]["metrics"]["harmony"] == pytest.approx(0.3)
    assert comparison["delta"]["metrics"]["friction"] == pytest.approx(-0.15)
    assert comparison["delta"]["directional_metrics"]["friction"] == pytest.approx(0.15)


def test_policy_passes_and_reports_every_failure() -> None:
    states = [observation("candidate", 0.7, 0.25)]
    passing = evaluate_policy(states, QualityPolicy(min_harmony=0.7, max_friction=0.25))
    assert passing.passed
    assert passing.to_dict()["failures"] == []

    failing = evaluate_policy(
        states,
        QualityPolicy(min_score=0.9, min_harmony=0.8, max_friction=0.1),
    )
    assert not failing.passed
    assert len(failing.failures) == 3
    assert "harmony" in " ".join(failing.failures)


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), True, "0.5"])
def test_policy_rejects_invalid_thresholds(value: object) -> None:
    with pytest.raises(UCFValidationError):
        QualityPolicy(min_score=value)  # type: ignore[arg-type]


def test_analysis_rejects_empty_and_invalid_inputs() -> None:
    with pytest.raises(UCFValidationError, match="at least one"):
        summarize_states([])
    with pytest.raises(UCFValidationError, match="UCFState"):
        summarize_states([object()])  # type: ignore[list-item]
    with pytest.raises(UCFValidationError, match="threshold"):
        QualityPolicy()
    with pytest.raises(UCFValidationError, match="QualityPolicy"):
        evaluate_policy([observation("candidate", 0.7)], object())  # type: ignore[arg-type]
