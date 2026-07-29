"""Record and summarize two local coordination-health observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ucf_protocol import MetricSet, UCFJournal, UCFState


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("example-ucf.db"))
    args = parser.parse_args()

    observations = [
        UCFState(
            metrics=MetricSet(0.55, 0.68, 0.60, 0.72, 0.28, 0.58),
            context="start of coordination window",
            agent="example",
        ),
        UCFState(
            metrics=MetricSet(0.67, 0.74, 0.71, 0.81, 0.16, 0.65),
            context="after impediment review",
            agent="example",
        ),
    ]

    with UCFJournal(args.database) as journal:
        for observation in observations:
            journal.record(observation)
        latest = journal.latest()
        summary = journal.summary(limit=20)

    assert latest is not None
    print(latest.to_json())
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
