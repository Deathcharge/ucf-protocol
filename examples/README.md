# Examples

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
