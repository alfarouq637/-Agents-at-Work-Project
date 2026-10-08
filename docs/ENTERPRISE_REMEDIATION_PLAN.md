# AutoCorp Enterprise Remediation and Evolution Plan

## Purpose

Evolve AutoCorp from a hackathon FastAPI prototype into a secure, Arabic-first,
multi-tenant platform that lets Egyptian SMEs create, operate, and publish
responsive, accessible web applications. This document is intentionally honest
about the current implementation: features are promoted only after they are
implemented, tested, and observable in production.

## Evidence-Based Baseline (2026-10-07)

### Product assets reviewed

- Python/FastAPI application with a 3,728-line, 220 KB single-page dashboard.
- Six application modules plus builder, generator, Telegram, LLM, database, and
  SAST modules; 71 role definitions across 11 departments (not 70/10).
- SQLite development database, Turso HTTP fallback, generated demo sites, and
  static exports.
- Three pitch/submission PDFs and three product walkthrough videos. They confirm
  the target: bilingual Egyptian SME storefronts, portfolio sites, customer
  intake through Telegram, local payment methods, and self-service delivery.
- One AutoCorp mascot/brand image, duplicated in three locations.

### What works today

- A client can register, create a brief, receive a template-driven storefront,
  manage catalogue data, and export a generated Node/Express starter project.
- Telegram accepts text, documents, and photos; it can create a template site
  and send status messages.
- LLM providers have basic fallback and cooldown logic.
- The dashboard supports AR/EN presentation, theme preference, site editing,
  simple marketing drafts, and GitHub/Vercel export workflows.

### Remediation progress (local implementation, not a production attestation)

- Phase-0 containment now fails closed when the session signing secret is
  absent; browser sessions are signed HttpOnly cookies, local passwords use
  Argon2id with legacy-login migration, risky prototype endpoints are disabled
  by default, and protected operations have a
  structured audit trail. Each signed browser session also has a durable,
  per-session revocation record, so logout invalidates a copied token before
  its normal expiry.
- Public orders are rate-limited, replay-protected, use server-side catalog
  price snapshots, and remain `pending_confirmation`. No order is represented
  as paid or gateway confirmed. Signed, idempotent gateway webhooks and
  reconciliation remain required before enabling payment processing.
- Generated storefronts no longer display manual payment destinations or
  fabricate a successful checkout. Public site metadata does not expose
  integration configuration, and catalog values are encoded for their actual
  HTML/JavaScript context.
- Generated Node/Express exports no longer include a `.env`, default JWT
  secret, seeded user accounts, fallback login password, wildcard CORS, or
  merchant payment destinations. Deployment configuration and initial account
  provisioning remain explicit operator responsibilities.
- These improvements are covered by isolated regression tests, but they do
  not replace the deployment, secret-rotation, migration, or independent
  security gates below.
- Payroll ledger/balance/cost writes now share an atomic database transaction
  in the SQLite adapter and a conditional batch in the Turso HTTP adapter.
  Project planning also waits until the initial settings and catalog writes
  finish. These local primitives do not provide the planned PostgreSQL schema,
  transactional outbox, durable workflow recovery, or live-provider validation.

### Material gaps and risks

1. **Rotate all secrets before further work.** The README and deployment guide
   previously contained administrator and Telegram credentials; the dashboard
   also handled credentials in browser-side code. Treat the credentials as
   compromised; revoke/rotate them and remove them from Git history and Vercel
   logs. Never print credentials at startup.
2. **Identity is not production-safe yet.** The local password path now uses
   Argon2id and revocable HttpOnly sessions, but the application still needs a
   vetted OIDC provider, MFA/passkeys, recovery, device/session management,
   shared throttling, and production-grade CSRF controls before launch.
3. **Authorization and privacy are incomplete.** Job and artifact access now
   enforce the authenticated owner, and uploads have authentication, tenant
   binding, size, extension, and file-signature checks. They still lack
   malware scanning, object-storage isolation, retention enforcement, and
   database-enforced tenant policy. The global dashboard also retains many raw
   `innerHTML` calls that need a componentized, trusted rendering model.
4. **Payments are demonstrations, not payment integrations.** Orders now use
   server-side catalog price snapshots, idempotency keys, and a
   `pending_confirmation` state; they are not marked paid. A signed gateway
   webhook, payment ledger, amount/currency verification, reconciliation, and
   a complete payment-state machine are still absent. Do not claim live
   Paymob/Fawry/InstaPay/Vodafone Cash processing.
5. **Tenancy is virtual, not database-per-tenant.** Merchant records currently
   share the primary SQLite/Turso schema and are separated mainly by `job_id`.
   The downloadable tenant database can be generated from templates. This does
   not meet the advertised physical-isolation claim.
6. **The claimed full-stack output is largely generated text.** The platform
   exports Node/Express/Drizzle files but Vercel direct deploy sends only a
   static `index.html`. Generated project tests are not installed or run, and
   the in-app file inventory includes virtual files rather than a real workspace.
7. **The SAST grade is not a security certification.** It scans generated
   JavaScript patterns, not the FastAPI platform; it unconditionally marks some
   OWASP categories as passing and reported `100/A+` for a sample despite the
   platform vulnerabilities above.
8. **The system has no production reliability foundation.** A few multi-write
   paths now use local transactions, but there are no real worker queues,
   transactional outbox, durable workflow recovery, PostgreSQL migrations,
   production SLOs, structured telemetry, or disaster-recovery drills. CI
   lockfile/SBOM/security gates exist locally, but provider deployment and
   production operation are not verified. Vercel function invocations are
   unsuitable for durable long-running agent work.
9. **Accessibility and maintainability need deliberate work.** The duplicated
   dashboard has 198 inline event handlers, 69 `innerHTML` uses, no ARIA
   attributes, and an image without alternate text. `static/` and `api/static/`
   are byte-for-byte duplicates.

## Non-Negotiable Product Rules

- Protect a merchant's data from every other merchant by default; all service
  queries carry an authenticated tenant context and database-enforced policy.
- An AI model can propose and draft. It cannot independently move money, expose
  a secret, deploy production code, publish marketing, or alter data without an
  explicit, auditable authorization policy.
- A payment is only `paid` after a gateway-signed webhook is verified and the
  order amount/currency/idempotency key match server-side records.
- Generated sites must pass the same accessibility, security, performance, and
  deployment gates as the AutoCorp platform.
- Marketing requires lawful consent, proof of consent, unsubscribe handling,
  audience suppression, and human approval before dispatch.

## Target Architecture

Use a modular monolith for the stabilization release, then extract services only
when their bounded context, independent scaling need, and operational ownership
are real. The target is service-oriented, not a distributed monolith.

```text
Browsers / Telegram / Partner webhooks
              |
Cloudflare: DNS, CDN, WAF, Turnstile, rate limits, bot controls
              |
API gateway / BFF (REST now; versioned public API)
  |             |               |                |
Identity    Agency workflow   Site runtime     Merchant console
  |             |               |                |
PostgreSQL + Redis + object storage + message broker + secret manager
              |
Workers: generation | publishing | Telegram | payments | marketing | audit
              |
OTel Collector -> logs, metrics, traces, alerts, SIEM
```

### Bounded contexts and future services

| Context | Responsibility | Data ownership | Extraction trigger |
| --- | --- | --- | --- |
| Identity and access | OIDC, MFA/passkeys, roles, sessions, SCIM later | identity schema | Always isolated logically |
| Tenant control plane | organisations, plans, domains, entitlements | control-plane schema | Split before enterprise onboarding |
| Workflow orchestration | durable job state, approvals, retries, budgets | workflow schema | Extract once jobs are asynchronous |
| Generation sandbox | prompt assembly, template selection, validation, artifacts | immutable artifact store | Isolate before arbitrary generated code |
| Merchant runtime | catalog, cart, orders, customer accounts | per-tenant data plane | Independently deployable site runtime |
| Payments | gateway adapters, webhook verification, ledger, refunds | payment schema | Extract before live card/payment use |
| Messaging | Telegram, WhatsApp, email, notifications | integration credentials and outbox | Extract before per-merchant bot launch |
| Search/knowledge | approved sources, embeddings, citations | vector index and source metadata | Add only after grounded research is needed |

Start with a Python API plus a TypeScript web application in a monorepo. Prefer
PostgreSQL with row-level security for the first secure multi-tenant release;
use a separate database/cluster for regulated or enterprise tenants. Keep
PostgreSQL for transactional data, Redis for cache/rate-limit/session primitives,
S3-compatible object storage for uploads/artifacts, and a managed broker plus
durable workflow engine for background work. Do not use SQLite as the shared
production control-plane database.

## Delivery Plan

### Phase 0 — Containment and truthful public status (first 24 hours)

1. Put the public deployment in maintenance/read-only mode while preserving
   exported demo sites.
2. Revoke and replace Telegram, LLM, Turso, GitHub, Vercel, payment, webhook,
   and administrator secrets. Delete credentials from documentation, commits,
   build logs, and database records; use GitHub secret scanning and provider
   audit logs to confirm exposure scope.
3. Disable default credentials, `/admin <password>` Telegram authentication,
   unauthenticated job listing/detail APIs, database SQL runner, direct code
   editor, and token-in-query-string deploy status endpoint until redesigned.
4. Mark payment, database isolation, OWASP grade, deployment, and uptime claims
   as "prototype" where they are not verified. Preserve the pitch story but
   publish an implementation status matrix.
5. Back up the current SQLite database encrypted; record a cryptographic hash,
   access log, owner, and retention period. Do not copy customer data into demos.

Exit gate: secrets are rotated; no credential is in Git or documentation; an
external visitor cannot list another merchant's projects or upload a file.

### Phase 1 — Secure modular-monolith foundation (weeks 1–3)

1. Restructure into `apps/web`, `apps/api`, `workers`, `packages/contracts`,
   `packages/ui`, `infra`, `docs`, and `tests`. Delete generated/cache output
   from version control; retain media under `docs/assets` using Git LFS or
   release attachments.
2. Replace home-grown authentication with a vetted OIDC provider. Support
   email verification, recovery, TOTP/passkeys, organization membership, RBAC
   plus permissions, short-lived HttpOnly/Secure/SameSite cookies, rotation,
   session revocation, CSRF protection, rate limits, and audit events. If local
   passwords remain, use Argon2id with unique salts and current parameters.
3. Define Pydantic request/response models, explicit error envelopes, request
   IDs, idempotency keys, pagination, limits, and a versioned OpenAPI contract.
   Fail closed on absent tenant/user context.
4. Replace raw HTML construction and dashboard `innerHTML` with a component
   framework using automatic escaping; sanitize the strictly limited rich-text
   surfaces. Consolidate the duplicated static dashboard into a single build.
5. Build safe file ingestion: authorization before streaming, tenant-scoped
   object key, byte/MIME/signature allow-list, quota, image/PDF parsing sandbox,
   malware scan, EXIF stripping, content-disposition downloads, signed URLs,
   and lifecycle deletion.
6. Add PostgreSQL schema migrations (Alembic), foreign keys, indexes, unique
   idempotency constraints, transaction boundaries, outbox records, encryption
   key references, and backup/restore tests.

Exit gate: dependency lockfiles, migration tests, unit/integration tests,
authorization test matrix, and zero high/critical findings in authenticated
DAST/SAST dependency scans.

### Phase 2 — Real multi-tenancy, commerce, and builder (weeks 4–7)

1. Model `organisation`, `membership`, `merchant`, `site`, `environment`,
   `domain`, `artifact`, `catalog`, `order`, `payment`, `integration`, and
   `audit_event`. Enforce tenant isolation twice: repository query predicates
   and PostgreSQL RLS using a transaction-scoped tenant ID.
2. Implement a domain-driven site specification (JSON Schema) as the source of
   truth. The generator compiles it into a versioned site artifact, rather than
   persisting arbitrary mutable HTML. Keep every artifact immutable, signed,
   scanable, previewable, promotable, and rollbackable.
3. Ship responsive templates from one accessible design system: semantic HTML,
   keyboard/focus states, skip links, logical CSS properties for RTL, reduced
   motion, localization, image dimensions, dark-mode contrast, and WCAG 2.2 AA
   automated/manual checks at 320 px, 768 px, 1024 px, and 1440 px.
4. Introduce a factual payment state machine: `draft -> pending -> authorized
   -> paid/failed/refunded/cancelled`; calculate totals on the server from price
   snapshots; validate signed webhooks; make webhooks idempotent; reconcile
   daily; retain an append-only financial ledger. Integrate each approved Egypt
   provider through its official APIs only after contractual/compliance review.
5. Make each exported project truthful: either ship a tested static export, or
   ship a complete runnable application with lockfile, migration, test suite,
   secret-free `.env.example`, SBOM, deployment guide, and CI pipeline. The
   Vercel route must never advertise a full-stack deployment when sending only
   static files.

Exit gate: cross-tenant access tests are negative; payment test-mode webhooks
are verified end-to-end; each generated artifact builds, passes security and
accessibility tests, and deploys to an isolated preview URL.

### Phase 3 — Durable automation and Telegram operations (weeks 8–10)

1. Replace in-process tasks and serverless fire-and-forget calls with queue
   workers and durable workflows. Every workflow has a state machine, retry
   policy, timeout, idempotency key, compensation action, budget ceiling, and
   human approval checkpoint.
2. Rebuild the Telegram bot as a channel adapter: webhook secret validation,
   organization/merchant binding, message deduplication in durable storage,
   conversation state, command authorization, consent capture, file quarantine,
   order status, escalation, and customer/owner notification preferences.
3. Store per-merchant Telegram/WhatsApp credentials encrypted with envelope
   encryption (KMS-managed data-encryption keys) and never return them through
   a GET endpoint. Use delegated/scoped provider credentials where supported.
4. Add an operations command centre: approval queues, incident controls, bot
   health, replay-safe webhook inspection, workflow trace view, merchant
   support timeline, and a global kill switch. The bot becomes the mobile
   operations surface, not a channel that holds a master password.
5. Automation improvements must be proposal-based: offline evaluation,
   sandbox, approval, canary, rollback, and complete provenance. No model may
   modify its own prompts/templates in production directly.

Exit gate: a worker loss, duplicate webhook, provider timeout, and Telegram
retry are demonstrably safe, observable, and recoverable.

### Phase 4 — Production platform, SRE, and enterprise controls (weeks 11–14)

1. Use a multi-environment CI/CD pipeline: protected branches, conventional
   migrations, unit/integration/contract/E2E/accessibility/load/security tests,
   SAST, secret scan, dependency/SBOM scan, container scan, IaC scan, signed
   artifacts, preview environments, canary release, and automatic rollback.
2. Host the control plane and workers on a managed container platform with
   separate service accounts and private networking; serve generated static
   sites through object storage/CDN. Keep Vercel only for suitable edge/static
   delivery, not durable orchestration.
3. Place Cloudflare in front of public services: managed WAF rules, Turnstile
   on sensitive forms, per-route rate limits, bot mitigation, DDoS protection,
   origin lockdown, TLS 1.3, HSTS, CSP (nonce/hash based), secure headers, and
   certificate automation.
4. Instrument API, workers, LLM providers, database, payment adapters, and
   Telegram with OpenTelemetry traces, structured logs, metrics, correlation
   IDs, PII redaction, SLO dashboards, alerts, on-call runbooks, and synthetic
   checkout/site-generation probes.
5. Set targets: 99.9% control-plane availability initially, RPO <= 15 minutes,
   RTO <= 4 hours, weekly encrypted backups, quarterly restore drills, regional
   outage runbook, capacity/cost alarms, and quarterly access review.

Exit gate: disaster recovery drill meets the RPO/RTO, SLO/error-budget alerts
work, least-privilege permissions are reviewed, and an independent security
assessment closes critical/high issues.

## AI, Research, and Self-Improvement Controls

- Create a policy decision point before every tool action. Tools receive only a
  scoped, expiring capability (for example, `draft_campaign` for one merchant),
  never the all-powerful process environment.
- Treat uploaded documents, web pages, retrieved text, and model output as
  untrusted data. Separate instructions from data, require allow-listed tool
  schemas, validate outputs, strip secrets/PII, set token and cost budgets, and
  require approvals for side effects.
- Build source-grounded research with URL, publisher, timestamp, excerpt hash,
  citation, and confidence. Do not let autonomous research publish claims.
- Maintain prompt/template versions, evaluation datasets, red-team cases for
  prompt injection and excessive agency, quality scores, approval evidence,
  and rollback history. Measure self-improvement before promotion.

## Security and Cryptography Baseline

- TLS 1.3 in transit; modern certificate automation and HSTS. Use managed KMS
  keys with rotation, key inventory, access audit, envelope encryption for
  integration secrets, and AES-256-GCM or ChaCha20-Poly1305 authenticated
  encryption at rest where application-layer encryption is required.
- Use CSPRNG identifiers/nonces, SHA-256/512 only for integrity as appropriate,
  Argon2id for passwords, and vetted libraries rather than custom cryptography.
- Target OWASP ASVS 5 Level 2 for the platform and OWASP LLM Top 10 (2025) for
  agent workflows. Replace the marketing-style score with a versioned control
  matrix tied to test evidence and human review.

## Documentation and Code Standard

- Keep modules small and owned by a bounded context. Comments explain *why*,
  security boundaries, data ownership, and non-obvious tradeoffs; types and
  names explain *what*. Avoid comment noise and do not disclose secrets.
- Maintain C4 diagrams, ADRs, OpenAPI/AsyncAPI contracts, threat models, data
  classification/retention maps, runbooks, deployment guide, and an honest
  feature-status matrix.
- Keep pitch/deck media as evidence of the original vision, but update all
  technical claims when implementation status changes.

## Initial Backlog Order

P0: secret rotation and public containment; remove insecure defaults; protect
jobs/uploads; disable unsafe admin/SQL/file/token paths.

P1: OIDC/session/RBAC, PostgreSQL migrations/RLS, safe uploads, component UI,
CI quality gates, real audit logs, and artifact-based site generation.

P2: payment adapters/webhooks, durable queues/workflows, encrypted bot
credentials, Telegram operations console, generated-app verification.

P3: service extraction, multi-region resilience, data warehouse/analytics,
enterprise SSO/SCIM, approved RAG/research, and governed optimization loops.

## External Standards Used

- OWASP ASVS 5 provides the application-security verification baseline:
  <https://owasp.org/projects/asvs>.
- OWASP LLM Top 10 (2025) informs model, prompt, supply-chain, and excessive-
  agency controls: <https://genai.owasp.org/llm-top-10/>.
- OpenTelemetry is the vendor-neutral standard for traces, metrics, and logs:
  <https://opentelemetry.io/docs/>.
- Vercel cron invocations have the same execution-duration limits as functions;
  durable agent work therefore belongs in workers/workflows:
  <https://vercel.com/docs/cron-jobs/manage-cron-jobs>.
- Cloudflare documents managed WAF, DDoS, bot, and rate-limit controls:
  <https://developers.cloudflare.com/waf/>.
