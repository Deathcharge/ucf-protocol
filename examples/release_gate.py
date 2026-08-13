"""Compare a baseline with a candidate and enforce a transparent release policy."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ucf_protocol import (
    MetricSet,
    QualityPolicy,
    UCFJournal,
    UCFState,
    compare_states,
    evaluate_policy,
)

UTC = timezone.utc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("release-gate.db"))
    args = parser.parse_args()
    start = datetime.now(UTC)
    baseline = [
        UCFState(
            metrics=MetricSet(0.58, 0.66, 0.63, 0.68, 0.29, 0.57),
            timestamp=start,
            context="baseline agent workflow",
            metadata={"correlation": {"release_id": "baseline"}},
        ),
        UCFState(
            metrics=MetricSet(0.61, 0.69, 0.65, 0.7, 0.26, 0.6),
            timestamp=start + timedelta(seconds=1),
            context="baseline agent workflow",
            metadata={"correlation": {"release_id": "baseline"}},
        ),
    ]
    candidate = [
        UCFState(
            metrics=MetricSet(0.7, 0.76, 0.74, 0.8, 0.18, 0.69),
            timestamp=start + timedelta(minutes=1),
            context="candidate agent workflow",
            metadata={"correlation": {"release_id": "candidate"}},
        ),
        UCFState(
            metrics=MetricSet(0.73, 0.79, 0.77, 0.82, 0.16, 0.71),
            timestamp=start + timedelta(minutes=1, seconds=1),
            context="candidate agent workflow",
            metadata={"correlation": {"release_id": "candidate"}},
        ),
    ]

    with UCFJournal(args.database) as journal:
        import_result = journal.record_many([*baseline, *candidate])

    comparison = compare_states(baseline, candidate)
    gate = evaluate_policy(
        candidate,
        QualityPolicy(min_score=0.7, min_harmony=0.68, max_friction=0.2),
    )
    print(
        json.dumps(
            {"import": import_result.to_dict(), "comparison": comparison, "gate": gate.to_dict()},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if gate.passed else 5


if __name__ == "__main__":
    raise SystemExit(main())
