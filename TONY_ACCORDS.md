# Tony Accords: project values

The Tony Accords capture Samsarix's ethical intent. In this repository they are design
values, not an automated enforcement, monitoring, consensus, or consciousness system.

## Four values

### Nonmaleficence

Avoid foreseeable harm. Bound untrusted input, preserve user data, fail visibly, protect privacy, and
prefer reversible actions. Security-sensitive decisions require evidence and human review.

### Autonomy

Respect the agency of users and contributors. UCF does not make decisions for its operator, transmit
observations, or silently change data. The operator chooses what to record, where to store it, and how
to interpret it.

### Compassion

Design for real people. Error messages should explain the next step; documentation should not shame
new users or overstate certainty. Community participation follows the
[code of conduct](CODE_OF_CONDUCT.md).

### Humility

State limitations plainly. UCF metrics are subjective inputs and the composite score is an
unvalidated heuristic. Phase labels are shorthand, not claims about consciousness, psychology,
morality, or objective team performance.

## Product implications

These values currently appear in verifiable engineering choices:

- a local-only runtime with no telemetry, account, or third-party runtime dependency;
- strict validation, duplicate protection, bounded reads, and fail-closed database revalidation;
- explicit filesystem and confidentiality limitations in [SECURITY.md](SECURITY.md);
- transparent metric and score definitions in [UCF_METRICS.md](UCF_METRICS.md);
- a release candidate instead of an unsupported production-readiness claim;
- tests and CI that exercise success, empty, invalid, corrupted, and interrupted paths.

They do not imply that named autonomous agents, ethical overrides, real-time sentiment analysis,
collective voting, audit archives, or compliance scores are implemented by this package. Such systems
would require separate specifications, consent, security boundaries, evaluation, and operational
evidence.

## Decision questions

Before changing the protocol, ask:

1. What user outcome is intended, and who could be harmed?
2. Does the change preserve user control and data sovereignty?
3. Are failure, rollback, and privacy consequences clear?
4. What evidence supports the claim being made?
5. Which uncertainty or limitation must be documented?
6. Does the implementation match its documentation and tests?

When answers are uncertain or the impact extends beyond this local package, pause for explicit human
review. These values guide judgment; they do not replace applicable law, professional expertise,
security review, or informed consent.
