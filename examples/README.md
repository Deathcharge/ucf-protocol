# Examples

## Langfuse score adapter (offline)

```console
python examples/langfuse_adapter.py
```

Prints six keyword-argument objects for the documented Langfuse `create_score` method using the
packaged correlated fixture. The example requires no Langfuse installation or credentials and
never sends data. It maps span IDs to observation IDs, preserves stable score IDs for idempotency,
and retains raw friction values with a direction marker. It requires a trace or session target.

The mapping follows the [Langfuse score SDK documentation](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
and [Python API reference](https://python.reference.langfuse.com/langfuse), inspected 2026-08-31.
In an application that already owns a configured Langfuse client, pass each result of
`langfuse_score_arguments(state)` to `client.create_score(**arguments)` and flush the client before
shutdown. Configure bounded timeouts/retries in that application. Review correlation identifiers
before transmission and use real trace/session IDs in the intended project. This example's
offline tests validate mapping only; they do not prove remote acceptance or delivery. Do not run
the synthetic fixture against production. UCF remains usable without this optional integration.

`basic_journey.py` uses only the public Python API. It records two observations in a selected SQLite
journal, reads the latest observation, and prints a bounded summary:

```console
python -m pip install -e ".[dev]"
python examples/basic_journey.py --database example-ucf.db
```

The example generates event IDs, so running it again appends two new observations. Remove the example
database yourself when you no longer need it. For the CLI journey, follow
[docs/QUICKSTART.md](../docs/QUICKSTART.md).

`release_gate.py` demonstrates the product wedge end to end: it atomically records baseline and
candidate assessments with release correlation metadata, compares them, and applies an explicit
pass/fail policy:

```console
python examples/release_gate.py --database release-gate.db
```
