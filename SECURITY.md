# Security policy

## Supported version

`1.0.0rc1` is the only supported line while UCF Protocol is in release-candidate status. Security
fixes are made on the default branch and included in the next release candidate. No older version is
claimed to receive fixes.

## Reporting a vulnerability

Do not open a public issue for a vulnerability or attach private journal contents, credentials, or
personal data to an issue. Use GitHub's private vulnerability-reporting feature for this repository
if it is enabled. If it is not available, contact the repository owner through an established private
channel and include only the minimum reproduction needed. The project does not yet promise a response
SLA; establishing a durable private contact and response policy is a gate for general availability.

Please include the affected version, platform and Python version, impact, prerequisites, a minimal
reproduction, and any suggested remediation. Give maintainers a reasonable opportunity to validate
and fix the issue before public disclosure.

## Product security model

### Assets

- confidentiality of user-supplied context and metadata;
- integrity and availability of observation history;
- correctness of metric, phase, score, and export data;
- integrity of built distributions and the CI process.

### Trust boundaries and attacker capabilities

UCF runs with the invoking user's filesystem permissions. CLI arguments, environment variables,
database/export paths, JSON files, stdin, metadata, and pre-existing SQLite contents are untrusted.
A malicious local input producer may try to exhaust memory/disk, inject SQL, corrupt derived values,
overwrite files, or trigger ambiguous parsing. A same-user process can directly read or modify the
journal and is outside the protection the package can provide.

The supported runtime opens no network listener, sends no network traffic, loads no third-party
plug-ins, and has no third-party dependencies. There are no server authentication, authorization,
session, browser, or transport boundaries in this repository.

### Controls

- Strict `ucf/v1` parsing rejects unknown fields, non-finite/out-of-range metrics, invalid derived
  values, malformed timestamps, oversized input, and deeply nested or oversized metadata.
- SQLite statements bind values as parameters, schema constraints enforce metric ranges, duplicate
  event IDs fail closed, reads are bounded, and stored rows are revalidated.
- Export refuses replacement by default and uses a temporary file plus same-filesystem atomic replace.
- CI uses pinned action commits, least-privilege read permissions, strict lint/type checks, a branch
  coverage gate, distribution validation, and clean-wheel smoke installation.
- The product does not collect credentials or telemetry and does not silently transmit journal data.

### Limitations and operator responsibilities

The journal is not encrypted, signed, access-controlled beyond filesystem permissions, tamper-proof,
or suitable as an audit log against a local adversary. Use appropriate OS permissions and disk
encryption, keep tested backups, and choose retention and secure-deletion procedures. Do not record
secrets, authentication tokens, regulated data, or unnecessary personal information in free-form
fields.

SQLite is for local use, not a hostile multi-tenant or multi-host service. Export destinations are
chosen by the operator; `--force` deliberately authorizes replacement. Installing a wheel still
requires normal Python supply-chain controls: verify its source, provenance, and hash when those are
available.

## Out of scope

Security claims about hosted Helix APIs, dashboards, Discord bots, Redis, cloud platforms, or other
repositories are out of scope. They are not part of this product or security boundary.
