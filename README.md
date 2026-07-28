# UCF Protocol

[![CI](https://github.com/Deathcharge/ucf-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/Deathcharge/ucf-protocol/actions/workflows/ci.yml)

UCF Protocol is a local-first Python library and command-line tool for recording explicit
coordination-health observations. It validates six normalized signals, derives a transparent score
and phase, stores observations in SQLite, and exports versioned JSON Lines.

It runs without an account, network service, or third-party runtime dependency.

> UCF signals are subjective, user-supplied operational assessments. They are not scientific
> measurements of consciousness, medical or psychological measures, or replacements for logs,
> traces, service-level indicators, and other objective telemetry.

## Install from this checkout

Python 3.10 or newer is required. Use a virtual environment:

```console
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install .
ucf --version
```

The current version is a release candidate. This repository does not publish automatically.

## Complete first journey

Record an observation in an explicitly chosen local journal:

```console
ucf --database ucf-demo.db record \
  --event-id release-check-1 \
  --harmony 0.65 \
  --resilience 0.72 \
  --throughput 0.70 \
  --focus 0.80 \
  --friction 0.18 \
  --velocity 0.62 \
  --context "pre-release review" \
  --agent "operator"
```

PowerShell accepts the same command on one line. Then inspect and export it:

```console
ucf --database ucf-demo.db status
ucf --database ucf-demo.db history --json
ucf --database ucf-demo.db summary
ucf --database ucf-demo.db export --output observations.jsonl
```

`init` is optional because every journal command initializes the database safely. Running
`status` against an empty journal returns an actionable message and exit code 3. Run
`ucf <command> --help` for command-specific options.

## Python API

```python
from ucf_protocol import MetricSet, UCFJournal, UCFState

observation = UCFState(
    metrics=MetricSet(
        harmony=0.65,
        resilience=0.72,
        throughput=0.70,
        focus=0.80,
        friction=0.18,
        velocity=0.62,
    ),
    event_id="release-check-1",
    context="pre-release review",
    agent="operator",
)

with UCFJournal("ucf-demo.db") as journal:
    journal.record(observation)
    latest = journal.latest()
    assert latest is not None
    print(latest.to_json())
```

All six metrics must be finite numbers in `[0, 1]`. Lower friction is better; the other five
signals are positive. The exchange contract is `ucf/v1`; its JSON Schema ships inside the wheel.

## Documentation

- [Quick start](docs/QUICKSTART.md)
- [Metric and scoring contract](UCF_METRICS.md)
- [CLI and Python API](docs/API.md)
- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Local operation and release](docs/DEPLOYMENT.md)
- [Security policy](SECURITY.md)
- [Productization evidence](docs/PRODUCTIZATION.md)

## Development

```console
python -m pip install -e ".[dev]"
ruff format --check src tests examples
ruff check src tests examples
mypy src
pytest
python -m build
python -m twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for compatibility and change requirements.

## License and release status

Package metadata identifies the reusable Python core as Apache-2.0; see [LICENSE](LICENSE).
The repository also contains pre-existing [commercial licensing guidance](LICENSING.md) and a
[proprietary license](LICENSE.PROPRIETARY). Their public-release positioning requires owner/legal
confirmation and is not resolved by this technical release candidate.
