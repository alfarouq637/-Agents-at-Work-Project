# Application Boundaries

AutoCorp is still a modular monolith. It is **not** a microservices deployment
yet. The immediate goal is to establish stable ownership boundaries and
contracts before moving data or asynchronous work across a network.

## Current extracted boundary

`app/routers/operations.py` owns internal operational HTTP routes:

- operational summaries and ledger views;
- agent/roster and provider status;
- post and proposal review decisions.

It uses signed administrator sessions and preserves the original `/api/*`
routes, so the dashboard is not coupled to the source-file layout.

## Planned bounded contexts

| Context | Present location | Extraction destination | Data ownership |
| --- | --- | --- | --- |
| Identity and access | `app/auth.py` | Identity service | users, sessions, roles |
| Operations control plane | `app/routers/operations.py`, `app/corp.py` | Operations/workflow service | jobs, approvals, audit events |
| Site generation | `app/builder.py`, `app/enterprise_generator.py` | Generation worker service | versioned specifications and artifacts |
| Merchant runtime | site routes in `app/main.py` | Merchant runtime service | catalog, orders, customers |
| Messaging | Telegram handlers in `app/main.py` | Messaging service | integration references, outbox events |
| Payments | payment routes in `app/main.py` | Payments service | gateway events and immutable ledger |

## Migration rules

1. Extract a boundary only after it has a tested API contract and a named data
   owner.
2. Workers communicate through versioned events and idempotency keys; they do
   not share the primary database directly.
3. Each service validates tenant and actor context at its own boundary.
4. Prototype endpoints remain disabled until their replacement has telemetry,
   retries, audit logging, and deployment checks.

The target network topology is detailed in
[ENTERPRISE_REMEDIATION_PLAN.md](../ENTERPRISE_REMEDIATION_PLAN.md).
