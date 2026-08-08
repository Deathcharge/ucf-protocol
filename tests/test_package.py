from __future__ import annotations

import json
from importlib import resources

import ucf_protocol
from ucf_protocol.model import PHASES


def test_public_api_and_version_are_deliberate() -> None:
    assert ucf_protocol.__version__ == "1.0.0rc1"
    assert ucf_protocol.__all__ == [
        "LEGACY_ALIASES",
        "METRIC_NAMES",
        "SCHEMA_VERSION",
        "DuplicateEventError",
        "JournalError",
        "MetricSet",
        "UCFJournal",
        "UCFProtocol",
        "UCFState",
        "UCFValidationError",
        "__version__",
        "default_database_path",
        "parse_timestamp",
        "phase_for_harmony",
        "state_from_json",
    ]


def test_json_schema_is_packaged_and_names_the_protocol() -> None:
    schema_file = resources.files("ucf_protocol").joinpath("schemas/ucf-state-v1.schema.json")
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == "ucf/v1"
    assert set(schema["required"]) == {"schema_version", "event_id", "timestamp", "metrics"}
    assert set(schema["properties"]["metrics"]["required"]) == set(ucf_protocol.METRIC_NAMES)
    assert schema["properties"]["phase"]["enum"] == [name for _, name in PHASES]
