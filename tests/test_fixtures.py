from __future__ import annotations

import json
from importlib import resources

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from ucf_protocol import UCFValidationError, state_from_json


def test_packaged_conformance_manifest_matches_parser_contract() -> None:
    fixture_root = resources.files("ucf_protocol").joinpath("fixtures")
    schema_root = resources.files("ucf_protocol").joinpath("schemas")
    manifest = json.loads(fixture_root.joinpath("manifest.json").read_text(encoding="utf-8"))
    schema = json.loads(
        schema_root.joinpath("ucf-state-v1.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert manifest["schema_version"] == "ucf/fixtures/v1"
    assert {case["expect"] for case in manifest["cases"]} == {"valid", "invalid"}
    assert {case["schema_expect"] for case in manifest["cases"]} == {"valid", "invalid"}

    for case in manifest["cases"]:
        payload = fixture_root.joinpath(case["file"]).read_text(encoding="utf-8")
        schema_errors = list(validator.iter_errors(json.loads(payload)))
        assert bool(schema_errors) is (case["schema_expect"] == "invalid"), case["file"]
        if case["expect"] == "valid":
            assert state_from_json(payload).event_id.startswith("fixture-")
        else:
            with pytest.raises(UCFValidationError):
                state_from_json(payload)
