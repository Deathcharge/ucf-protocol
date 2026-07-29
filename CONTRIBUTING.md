# Contributing

UCF Protocol favors small, auditable changes that keep the local core dependable and honest.

## Set up

Use Python 3.10 or newer in a virtual environment:

```console
python -m venv .venv
# activate the environment for your shell
python -m pip install -e ".[dev]"
```

## Required checks

Run these from the repository root before opening a pull request:

```console
ruff format --check src tests examples
ruff check src tests examples
mypy src
pytest
python -m build
python -m twine check dist/*
```

CI repeats the static and test checks across Python 3.10 through 3.14 and smoke-installs the wheel.
Do not weaken a gate to make a change pass; update the implementation or explain a deliberate policy
change in the pull request.

## Compatibility rules

- Treat `ucf/v1` serialized fields, metric ranges, phase boundaries, and CLI exit codes as public
  contracts.
- Additive metadata usage does not require a schema version. Removing or reinterpreting fields does.
- Keep runtime dependencies at zero unless the feature cannot be implemented safely with the standard
  library and the maintenance cost is justified.
- Bound user-controlled input, queries, and output operations.
- Never add network transmission, telemetry, credentials, or hosted-service assumptions silently.
- Examples must run in CI and must use only shipped APIs.
- Describe coordination signals as subjective inputs; do not make scientific, medical, or
  consciousness-measurement claims.

## Tests and documentation

Every behavior change needs a focused test, including an error path when relevant. Update the README,
API contract, metric contract, changelog, and JSON Schema together when their promises change. The
suite enforces at least 90% branch coverage, but meaningful assertions matter more than the number.

## Security reports

Do not open a public issue for a suspected vulnerability or include secrets/private journal data in
test fixtures. Follow [SECURITY.md](SECURITY.md).
