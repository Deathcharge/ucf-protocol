# Local operation and release

UCF Protocol is a library and CLI, not a hosted service. "Deployment" means installing an immutable
wheel into a controlled Python environment and choosing where its SQLite journal lives.

## Build an artifact

From a clean checkout with development dependencies installed:

```console
python -m pytest
ruff format --check src tests examples
ruff check src tests examples
mypy src
python -m build
python -m twine check dist/*
```

The build produces a wheel and source distribution in `dist/`. Inspect or smoke-install the wheel in
a new virtual environment before distributing it:

```console
python -m venv smoke-venv
smoke-venv/bin/python -m pip install dist/ucf_protocol-1.0.0rc1-py3-none-any.whl
smoke-venv/bin/ucf --version
```

On Windows, use `smoke-venv\Scripts\python.exe` and `smoke-venv\Scripts\ucf.exe`.

## Operate locally

Set `UCF_DATABASE` to an absolute, access-controlled path or pass `--database` on each command. Back
up the database with SQLite-aware tooling or while no writer is active; include the `-wal` file if a
live backup procedure requires it. Test restoration before relying on backups.

The runtime has no third-party packages, secrets, ports, background services, scheduled work, or
outbound traffic. Capacity is bounded mainly by local disk and SQLite characteristics. `history` and
`summary` cap individual queries; `export` streams all rows and may take time for a large journal.

## Upgrade and rollback

1. Back up the journal.
2. Install the new wheel in a fresh environment.
3. Run `ucf --database PATH init`; unsupported future schema versions fail visibly.
4. Run `status`, `summary`, and a non-destructive export smoke test.
5. Switch the invoking script or shell to the new environment.

Rollback by returning to the previous environment. Do not assume a newer database schema is backward
compatible unless the release notes explicitly say so.

## Publication gates

This repository intentionally has CI but no automated package-publication workflow. Before a public
general-availability release, maintainers must:

- reconcile the Apache, proprietary, and commercial licensing files with owner/legal counsel;
- approve the package name, version, support policy, and release notes;
- configure trusted publishing and artifact signing/provenance if desired;
- create the release and verify the published artifact from an unrelated clean environment.

Do not put publishing credentials in the repository or local command history.
