from __future__ import annotations

import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from ucf_protocol import METRIC_NAMES, MetricSet, UCFState, UCFValidationError
from ucf_protocol.scores import score_records


def test_packaged_score_schema_enforces_values_and_direction() -> None:
    schema = json.loads(
        files("ucf_protocol").joinpath("schemas/ucf-score-v1.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    rows = score_records(UCFState(MetricSet(0, 1, 0, 1, 1, 0)))
    for row in rows:
        validator.validate(row)
        assert not validator.is_valid({**row, "higher_is_better": not row["higher_is_better"]})
        assert not validator.is_valid({**row, "value": 1.1})
        assert not validator.is_valid({**row, "correlation": {"secret": "not allowed"}})


def test_scores_preserve_identity_direction_and_only_allowlisted_metadata() -> None:
    state = UCFState(
        MetricSet(0.7, 0.8, 0.6, 0.9, 0.2, 0.5),
        event_id="release-1",
        context="private notes",
        agent="private reviewer",
        metadata={"secret": "do not export", "correlation": {"trace_id": "trace-1", "secret": "x"}},
    )
    rows = score_records(state)
    assert len(rows) == 6
    assert [row["name"] for row in rows] == [f"ucf.{name}" for name in METRIC_NAMES]
    for name, row in zip(METRIC_NAMES, rows, strict=True):
        assert row["id"] == f"release-1:{name}"
        assert row["value"] == getattr(state.metrics, name)
        assert row["higher_is_better"] == (name != "friction")
        assert row["correlation"] == {"trace_id": "trace-1"}
        assert "private" not in str(row)
        assert "secret" not in str(row)
    rows[0]["correlation"]["trace_id"] = "changed"
    assert rows[1]["correlation"]["trace_id"] == "trace-1"
    assert score_records(state)[0]["correlation"]["trace_id"] == "trace-1"


@pytest.mark.parametrize("correlation", [None, [], {"trace_id": 1}, {"release_id": " "}])
def test_invalid_correlation_fails_explicitly(correlation) -> None:
    state = UCFState(MetricSet(0, 0, 0, 0, 0, 0), metadata={"correlation": correlation})
    with pytest.raises(UCFValidationError, match="correlation"):
        score_records(state)


def test_scores_work_without_correlation_and_reject_non_states() -> None:
    assert score_records(UCFState(MetricSet(1, 1, 1, 1, 1, 1)))[0]["correlation"] == {}
    with pytest.raises(UCFValidationError, match="UCFState"):
        score_records(None)  # type: ignore[arg-type]
