# Security Policy

## Current posture

AutoCorp is in active remediation and must not be treated as an independently
certified production platform. The current containment status is recorded in
[docs/PHASE0_CONTAINMENT_STATUS.md](docs/PHASE0_CONTAINMENT_STATUS.md).

## Reporting a vulnerability

Do not open a public issue containing credentials, customer data, exploit
details, or proof-of-concept payloads. Report the issue privately to the
project owner with:

- a concise impact description;
- the affected route, component, or generated artifact type;
- minimal reproduction steps; and
- any mitigation already applied.

Rotate exposed credentials immediately; do not wait for a code fix or release.

## Security release gate

Before public deployment, the owner must verify secret rotation, configuration
readiness, test/CI success, dependency review, deployment configuration, and
the Phase 0 exit criteria. A green static-review result is not a penetration
test or compliance certification.
