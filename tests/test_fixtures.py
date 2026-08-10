from __future__ import annotations

import json
from importlib import resources

import pytest

from ucf_protocol import UCFValidationError, state_from_json


def test_packaged_conformance_manifest_matches_parser_contract() -> None:
    fixture_root = resources.files("ucf_protocol").joinpath("fixtures")
    manifest = json.loads(fixture_root.joinpath("manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "ucf/fixtures/v1"
    assert {case["expect"] for case in manifest["cases"]} == {"valid", "invalid"}

    for case in manifest["cases"]:
        payload = fixture_root.joinpath(case["file"]).read_text(encoding="utf-8")
        if case["expect"] == "valid":
            assert state_from_json(payload).event_id.startswith("fixture-")
        else:
            with pytest.raises(UCFValidationError):
                state_from_json(payload)
