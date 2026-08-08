"""Public API for the UCF Protocol local observation journal."""

from ._version import __version__
from .analysis import GateResult, QualityPolicy, compare_states, evaluate_policy, summarize_states
from .journal import DuplicateEventError, JournalError, UCFJournal, default_database_path
from .model import (
    LEGACY_ALIASES,
    METRIC_NAMES,
    SCHEMA_VERSION,
    MetricSet,
    UCFProtocol,
    UCFState,
    UCFValidationError,
    parse_timestamp,
    phase_for_harmony,
    state_from_json,
)

__all__ = [
    "LEGACY_ALIASES",
    "METRIC_NAMES",
    "SCHEMA_VERSION",
    "DuplicateEventError",
    "GateResult",
    "JournalError",
    "MetricSet",
    "QualityPolicy",
    "UCFJournal",
    "UCFProtocol",
    "UCFState",
    "UCFValidationError",
    "__version__",
    "default_database_path",
    "compare_states",
    "evaluate_policy",
    "parse_timestamp",
    "phase_for_harmony",
    "state_from_json",
    "summarize_states",
]
