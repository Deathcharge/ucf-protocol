# UCF metric contract

UCF Protocol records six finite, dimensionless values in the closed interval `[0, 1]`. Values are
supplied by a user or an upstream process; the package does not infer or measure them.

| Metric | Interpretation | Direction |
| --- | --- | --- |
| `harmony` | Degree of alignment among participants or work streams | Higher is better |
| `resilience` | Ability to continue or recover when coordination is disrupted | Higher is better |
| `throughput` | Perceived flow of useful work through the coordination process | Higher is better |
| `focus` | Clarity and concentration on the current objective | Higher is better |
| `friction` | Coordination overhead, conflict, or impediment | Lower is better |
| `velocity` | Perceived pace of progress toward the current objective | Higher is better |

These definitions are intentionally operational and subjective. A team should define how it assigns
values before comparing observations. Values from different teams, rubrics, or time windows are not
automatically comparable.

## Composite score

The score is an unweighted arithmetic mean, with friction inverted:

```text
score = (harmony + resilience + throughput + focus + (1 - friction) + velocity) / 6
```

The score is always in `[0, 1]`. It is a transparent convenience heuristic, not a calibrated
predictor. Consumers should retain the six source values rather than treating the score as ground
truth.

## Harmony phase

The phase is derived only from `harmony`, preserving the protocol's phase semantics:

| Harmony interval | Phase |
| --- | --- |
| `[0.00, 0.30)` | `CRITICAL` |
| `[0.30, 0.45)` | `UNSTABLE` |
| `[0.45, 0.60)` | `COHERENT` |
| `[0.60, 0.80)` | `HARMONIOUS` |
| `[0.80, 1.00]` | `TRANSCENDENT` |

Phase labels are categorical shorthand, not diagnoses or claims about consciousness.

## Legacy aliases

The parser accepts four historical names at the metric-mapping boundary:

| Legacy name | Canonical name |
| --- | --- |
| `prana` | `throughput` |
| `drishti` | `focus` |
| `klesha` | `friction` |
| `zoom` | `velocity` |

Serialized `ucf/v1` observations always emit canonical names. Supplying both an alias and its
canonical name is rejected as ambiguous.
