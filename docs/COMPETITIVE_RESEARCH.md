# Competitive research and product wedge

Research date: 2026-08-08

## Decision

UCF Protocol should be a **local-first coordination assessment and release-gating protocol**, not a
general-purpose tracing platform. Its useful boundary is the judgment layer between operational
telemetry and a release decision:

1. people or automated evaluators record the same six bounded coordination signals;
2. UCF validates and preserves those assessments in a portable, versioned format;
3. teams compare a baseline with a candidate and apply an explicit pass/fail policy; and
4. optional adapters correlate UCF events with traces, sessions, experiments, or releases managed
   elsewhere.

This is a product hypothesis, not a claim that the six signals are scientifically validated.

## What established products already cover

### Evaluation and observability platforms

- [Langfuse scores](https://langfuse.com/docs/evaluation/scores/overview) attach numeric,
  categorical, boolean, or text evaluations to traces, observations, sessions, and dataset runs.
  Langfuse also provides dashboards, APIs, score configurations, and multiple evaluation sources.
- [Arize Phoenix](https://arize.com/docs/phoenix) combines OpenTelemetry/OpenInference tracing,
  evaluations, human labels, datasets, and experiments. Its
  [annotation model](https://arize.com/docs/phoenix/tracing/concepts-tracing/annotations-concepts)
  supports span- and document-level labels, scores, explanations, and human, LLM, or code sources.
- [OpenAI Evals](https://developers.openai.com/api/docs/guides/evals) defines an evaluation loop
  around a task, test data, and result analysis, with JSON Schema-backed inputs and JSONL datasets.
  It is provider-specific, and the documentation currently directs new users toward Datasets as
  the legacy Evals platform approaches retirement.

UCF should integrate with these systems instead of rebuilding their ingestion pipelines, hosted
dashboards, trace stores, model graders, or experiment managers.

### Standards

[OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) standardize
telemetry names and structure. Generative-AI conventions now live in a
[dedicated specification repository](https://github.com/open-telemetry/semantic-conventions),
which reinforces that trace correlation should use external standard identifiers. Those
conventions do not define UCF's subjective, multidimensional coordination rubric.

## Product gap UCF can occupy

| User need | Existing platform strength | UCF opportunity |
| --- | --- | --- |
| Trace and inspect an agent run | Strong | Correlate, do not duplicate |
| Store arbitrary evaluator scores | Strong | Supply a stable six-signal rubric |
| Work offline or in restricted environments | Often secondary | No account, service, or runtime dependency |
| Move assessments between tools | Platform-specific exports | Versioned JSONL plus conformance fixtures |
| Decide whether a candidate is healthier than a baseline | Usually custom analysis | Deterministic compare and policy commands |
| Explain why a release passed or failed | Flexible but non-standard | Transparent deltas and explicit thresholds |

## Ranked real use cases

1. **Agent or prompt release gate.** Reviewers assess baseline and candidate runs; CI fails when a
   declared threshold or regression tolerance is missed.
2. **Before/after operational review.** Import observations from two time windows and produce a
   deterministic change report for an incident response, process change, or team intervention.
3. **Portable annotation companion.** Preserve a stable coordination assessment beside a Langfuse
   trace, Phoenix span, OpenTelemetry trace, or provider experiment through metadata identifiers.
4. **Air-gapped evaluation journal.** Collect assessments where sending traces or prompts to a
   hosted service is unacceptable.

## Build sequence

### Competitive foundation

- Atomic, bounded JSONL import with dry-run and explicit duplicate handling.
- Baseline-versus-candidate comparison over explicit time windows.
- Machine-readable policy checks with stable exit codes for CI.
- A metadata convention for trace, span, session, experiment, release, and evaluator identifiers.
- Valid, invalid, boundary, and round-trip conformance fixtures.

### Interoperability proof

- Generic long-form score export that maps one UCF observation to six score records.
- One documented Phoenix or Langfuse adapter example that depends only on public contracts.
- A complete example: JSONL import, comparison, gate, report, and export.

### Later, only with evidence

- Signed assessment bundles and provenance attestations.
- Configurable rubric profiles under a new schema version.
- A hosted collaboration product, only after local workflows show repeat usage.

## Explicit non-goals

- Distributed tracing storage, prompt capture, or an OpenTelemetry collector.
- A hosted dashboard in the reference package.
- An LLM-as-judge framework or model-provider SDK.
- Employee surveillance, psychological scoring, or claims to measure consciousness.
- Silent weighting changes or opaque pass/fail decisions.

## Success evidence

The wedge is supported when an unfamiliar user can install the package, import a bounded JSONL
assessment set, compare two candidate windows, run a documented CI gate, correlate results to an
external run, and reproduce the same output without a network connection.
