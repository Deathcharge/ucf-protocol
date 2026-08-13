"""Deterministic comparison and policy evaluation for UCF observations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .model import METRIC_NAMES, UCFState, UCFValidationError


def _average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def summarize_states(states: Iterable[UCFState]) -> dict[str, Any]:
    """Return deterministic averages for a non-empty observation collection."""

    observations = list(states)
    if not observations:
        raise UCFValidationError("analysis requires at least one observation")
    if any(not isinstance(state, UCFState) for state in observations):
        raise UCFValidationError("analysis values must be UCFState observations")
    return {
        "count": len(observations),
        "score": _average([state.score for state in observations]),
        "metrics": {
            name: _average([getattr(state.metrics, name) for state in observations])
            for name in METRIC_NAMES
        },
    }


def compare_states(baseline: Iterable[UCFState], candidate: Iterable[UCFState]) -> dict[str, Any]:
    """Compare average candidate values with a baseline using transparent deltas."""

    baseline_summary = summarize_states(baseline)
    candidate_summary = summarize_states(candidate)
    metric_deltas = {
        name: candidate_summary["metrics"][name] - baseline_summary["metrics"][name]
        for name in METRIC_NAMES
    }
    return {
        "baseline": baseline_summary,
        "candidate": candidate_summary,
        "delta": {
            "score": candidate_summary["score"] - baseline_summary["score"],
            "metrics": metric_deltas,
            "directional_metrics": {
                name: (-delta if name == "friction" else delta)
                for name, delta in metric_deltas.items()
            },
        },
    }


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    """Explicit average-value thresholds used by a deterministic quality gate."""

    min_score: float | None = None
    min_harmony: float | None = None
    min_resilience: float | None = None
    min_throughput: float | None = None
    min_focus: float | None = None
    max_friction: float | None = None
    min_velocity: float | None = None

    def __post_init__(self) -> None:
        configured = False
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value is None:
                continue
            configured = True
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise UCFValidationError(f"{name} must be a number between 0 and 1")
            normalized = float(value)
            if not 0.0 <= normalized <= 1.0:
                raise UCFValidationError(f"{name} must be between 0 and 1")
            object.__setattr__(self, name, normalized)
        if not configured:
            raise UCFValidationError("quality policy requires at least one threshold")

    def to_dict(self) -> dict[str, float]:
        """Return only configured policy thresholds."""

        return {
            name: value
            for name in self.__dataclass_fields__
            if (value := getattr(self, name)) is not None
        }


@dataclass(frozen=True, slots=True)
class GateResult:
    """Machine-readable result from applying a quality policy."""

    passed: bool
    summary: Mapping[str, Any]
    policy: Mapping[str, float]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable gate result."""

        return {
            "passed": self.passed,
            "summary": dict(self.summary),
            "policy": dict(self.policy),
            "failures": list(self.failures),
        }


def evaluate_policy(states: Iterable[UCFState], policy: QualityPolicy) -> GateResult:
    """Apply configured thresholds to average values without hidden weighting."""

    if not isinstance(policy, QualityPolicy):
        raise UCFValidationError("policy must be a QualityPolicy")
    summary = summarize_states(states)
    actual = {"score": summary["score"], **summary["metrics"]}
    failures: list[str] = []
    for threshold_name, threshold in policy.to_dict().items():
        direction, metric_name = threshold_name.split("_", 1)
        value = actual[metric_name]
        if direction == "min" and value < threshold:
            failures.append(f"{metric_name} {value:.6f} is below minimum {threshold:.6f}")
        elif direction == "max" and value > threshold:
            failures.append(f"{metric_name} {value:.6f} exceeds maximum {threshold:.6f}")
    return GateResult(
        passed=not failures,
        summary=summary,
        policy=policy.to_dict(),
        failures=tuple(failures),
    )
