# UCF Protocol roadmap

This roadmap separates four gates: merge, release, publication, and flagship adoption. Passing one does not imply the next.

## Product boundary

Portfolio role: **protocol or specification**. UCF Protocol should remain implementation-independent, versioned, and fixture-driven. Samsarix Unified should prove compatibility through public conformance fixtures rather than private imports or copied application code.

Current disposition: merge the productized branch as a labeled reference specification. Do not describe the protocol as stable or scientifically validated until its schemas, compatibility rules, and evidence justify those claims.

## Stabilize the productized default

- Keep the default branch buildable from a clean checkout and preserve exact-head CI evidence.
- Reconcile repository, package, documentation, and dependency license obligations before publication.
- Replace stale Helix deployment links and fictional operational claims with historical labels or current, verified Samsarix references.
- Separate philosophical framing from normative protocol requirements so implementers can identify what is testable.
- Define schema identifiers, version negotiation, compatibility promises, and an extension mechanism.

## Conformance release

- Publish versioned schemas plus valid, invalid, boundary, and migration fixtures.
- Build and install the wheel in a clean environment; verify the CLI and artifact contents.
- Add cross-version property tests for serialization, validation, and round trips.
- Document deprecation windows and how unknown fields, agent types, and metric revisions behave.
- Tag a reproducible reference release only after licensing and phase language are accurate.

## Samsarix adoption

- Implement one Samsarix Unified adapter against the public schema.
- Prove a round trip between that adapter and one independent client using the same fixture set.
- Keep authentication, authorization, persistence, privacy, and product policy in the consuming applications rather than the protocol package.
- Run a small comprehension study: an implementer unfamiliar with the repository should be able to build a conforming message without private guidance.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, conformance fixtures, consuming implementations, and rollback path are recorded in a pull request or release record. README claims must not exceed that evidence.
