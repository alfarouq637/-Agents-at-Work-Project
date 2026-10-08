# Phase 0 Containment Status

Updated: 2026-10-08

## Completed in the repository

- Removed hard-coded administrator and Telegram credentials from tracked code
  and documentation.
- Added a default-off `MAINTENANCE_MODE` switch for incident containment. When
  enabled, it keeps read-only pages and health checks available while rejecting
  every state-changing HTTP, Telegram, webhook, and generated-site request.
- Replaced browser-readable authentication tokens with signed, HttpOnly session
  cookies. Password hashes use Argon2id; successful legacy `scrypt` or HMAC
  password logins are upgraded automatically.
- Required authentication and owner checks for jobs, job details, and uploads.
- Added upload size, extension, and file-signature validation. PDF briefs are
  extracted as transient input and are not retained at public static URLs.
- Image uploads now receive a decoder-based type check, a 20-megapixel ceiling,
  orientation normalization, and metadata-stripping re-encoding before storage.
- Generated full-stack exports now reject placeholder JWT secrets, require an
  explicit production browser-origin list, keep JWTs out of login response
  bodies, mark API responses `no-store`, and run their container as a
  non-root user. Their production session cookie is now strict same-site and
  logout clears it using the same cookie scope.
- Hardened high-risk dashboard rendering paths: tenant text is serialized for
  inline handler arguments, generated links are scheme-checked, external tabs
  are isolated with `noopener noreferrer`, and file/table/image values are
  escaped or constrained before HTML insertion. The planned component rewrite
  remains necessary to remove the remaining legacy `innerHTML` surface.
- Site deletion now removes the tenant's unshared local image-upload copies while
  preserving files that another tenant still references.
- Web and Telegram deletion paths now share one complete tenant-data cleanup
  routine, including generated artifacts, temporary operational records, and
  idempotency state, while retaining audit evidence of the deletion request.
- Added portable indexes for tenant-scoped jobs, files, catalogs, orders,
  records, automations, posts, and cleanup/idempotency lookups. This improves
  the present SQLite/libSQL prototype; it is not a replacement for the planned
  PostgreSQL migration and row-level security.
- Added a transaction API for atomic multi-write operations across local SQLite
  and Turso's conditional HTTP batches, then used it for payroll ledger, agent,
  and job-cost updates. SQLite rollback and the generated Turso batch shape are
  unit-tested; execution against a live Turso database is still unverified.
- Deferred asynchronous planning until project settings, uploaded-brief
  metadata, and initial catalog items are saved, preventing the worker from
  racing ahead of the submitted wizard data. A regression test checks the
  stored state at the worker-start boundary.
- Added an opt-in local SQLite backup/restore utility using authenticated
  AES-256-GCM envelopes, explicit owner/retention/key-reference metadata,
  source and restore integrity checks, and no-overwrite behavior. Cloud/Turso
  backup automation and scheduled recovery drills remain outstanding.
- Added baseline response headers, same-origin protection for browser writes,
  and no-store caching for API responses. An HTTPS canonical origin now enables
  HSTS and `Secure` session cookies, while local HTTP development remains
  usable. The response policy also prohibits plugin content, framing, document
  base changes, and cross-origin form posts. A nonce/hash-based `script-src`
  policy remains blocked on removal of the legacy dashboard's inline handlers.
  The Vercel configuration applies the compatible baseline to directly served
  files, and newly exported Node/Vercel projects carry the same static-host
  policy.
- Limited Telegram approvals to the configured owner chat and removed Telegram
  password login and implicit administrator promotion. Account password commands
  are also rejected in Telegram chat.
- Disabled unsafe prototype surfaces by default: direct GitHub/Vercel deploy,
  tenant SQL console, arbitrary file editor, and per-tenant bot credentials.
- Changed background automation to require owner approval for delivery and
  external publishing. A configured Netlify token no longer publishes a site
  unless the controlled-test deployment switch is explicitly enabled.
- Made outbound automation webhooks opt-in, public-HTTPS-only, and HMAC-signed
  with a dedicated secret. The unsigned legacy Make webhook setting is ignored
  until it is migrated to the signed registry.
- Redacted stored bot tokens from integration API responses.
- Added regression tests for session handling, tenant isolation, uploads,
  cross-origin writes, credential redaction, and disabled prototype features.
- Added a secret-free `/api/healthz` readiness probe and matching local-startup
  warnings so a misconfigured deployment is visible without exposing secrets.
  Readiness also verifies Argon2id availability and a non-sensitive database
  query before a load balancer can treat the API as healthy. Vercel readiness
  additionally requires Turso configuration rather than accepting ephemeral
  SQLite storage. Enabled deployment or outbound-webhook automation also fails
  readiness when its required configuration is incomplete or webhook URLs are
  not HTTPS.
- Removed client-controlled `Host` from the deployed browser-write trust
  decision. Production writes now require the configured canonical or explicitly
  trusted origin; host-derived same-origin handling is limited to local
  development hosts.
- Added a process-local login throttle as an immediate password-spraying
  defence. It is explicitly a temporary measure until shared Redis limits are
  deployed.
- Started the modular-monolith migration by extracting protected internal
  operations routes into `app/routers/operations.py`; public routes and
  administrator-session behavior remain unchanged.
- Added generated-artifact safety/responsiveness checks and changed the SAST
  response to a truthful automated-static-review result rather than an OWASP
  certification claim. The dashboard now labels its heuristic score and
  per-category results as static-review evidence rather than displaying an A+
  security grade, OWASP certificate, or a claim that no vulnerabilities exist.
- Made catalog serialization script-safe in both the hosted-site and exported
  project generators, preventing tenant text from closing an inline script tag.
- Removed wildcard credentialed CORS from generated Node projects; their
  browser origins must now be configured explicitly.
- Added repository CI for compilation, regression tests, and the synchronized
  dashboard copies. CI also rejects high-confidence credential formats in
  Git-tracked UTF-8 text without printing their values. This is a baseline
  quality gate, not a deployment approval.
- Added a CI dependency advisory audit and weekly Dependabot patch-update
  proposals. Runtime and test dependencies now have reviewed, hash-locked
  resolution artifacts (`requirements.lock` and `requirements-dev.lock`), which
  Docker and CI consume with `--require-hashes`. A reproducible CycloneDX 1.7
  runtime SBOM is committed at `docs/sbom.cdx.json` and CI rejects a stale
  inventory. Provenance attestations and a formal release review remain needed
  before the Phase 1 release gate is complete.
- Reconciled the example environment into a single source of truth for each
  setting, with every publication, delivery, and outbound-webhook automation
  switch disabled by default.
- Hardened the container baseline: the application runs as an unprivileged
  service user and Docker build context excludes local secrets, databases,
  generated tenant files, and user media.
- Replaced the historical Vercel instructions with a fail-closed preview
  deployment guide, including the Telegram webhook secret-token setup.
- Reconciled the main README with the actual prototype boundaries for static
  review, shared-schema tenancy, generated artifacts, automation, and disabled
  high-risk tenant tooling.
- Removed placeholder telephone, WhatsApp, and manual-payment destinations from
  Telegram-created sites and generated storefront defaults.
- Disabled the demo payment-activation endpoint by default; it cannot mark a
  subscription paid until a signed gateway-webhook and ledger flow replaces it.
- Removed simulated revenue recording from project delivery. An approved site
  delivery now explicitly records that payment was not processed, rather than
  creating a fabricated paid invoice or ledger entry.
- Reconcile every signed session with the current account record so account
  deletion or role changes take effect without waiting for token expiry.
- Persist revocable session records so an explicit logout also invalidates a
  copied signed token, rather than only removing the browser cookie.
- Record successful logout and denied local/admin sign-in attempts in the audit
  trail without storing credentials, tokens, or attempted usernames.
- Extended local anti-brute-force controls to the administrator login path.
- Constrained tenant artifact paths, including read-only file retrieval, to a
  portable path below the authenticated tenant's own artifact directory.
- Added a structured audit-event foundation for account creation/login and
  administrator decisions, with an administrator-only recent-events endpoint.
- Made the public Telegram webhook fail closed without its secret header and
  removed query-string authentication from the scheduled-tick endpoint.
- Constrained Telegram attachment intake to validated JPEG images and PDFs with
  a 10 MB limit; PDF briefs are transient input instead of public static files.
  Telegram PDF extraction also has the same page/text bounds as web uploads.
- Added typed authentication request contracts and validated request IDs on all
  HTTP responses to support traceability and later API versioning. Security
  audit events now retain that correlation ID without storing credentials.
- Replaced the project-creation dictionary with a bounded wizard contract for
  text, catalog entries, discovery answers, and feature toggles. Unknown fields
  and oversized arrays are rejected, and clients can no longer force
  synchronous agent execution; hosting configuration controls execution mode.
- Bounded GitHub/Vercel deployment request fields, restricted Vercel hooks to
  the provider's HTTPS integration endpoint, and removed caller tokens from
  deployment-status lookup. Status remains unavailable until a server-managed
  provider installation can be bound to a tenant; the risky feature flag alone
  cannot activate that unfinished status path.
- Added a bounded Pydantic contract for public site orders and line items;
  unknown fields, malformed IDs, invalid quantities, and overlong customer data
  are rejected before order logic runs. Client-supplied totals and prices remain
  accepted only as bounded display hints and are never authoritative.
- Added an aggregate 12 MiB ASGI request-body cap that counts streamed chunks,
  so chunked requests cannot bypass the limit; the allowance includes multipart
  framing above the existing 10 MiB file-upload ceiling.
- Added a backward-compatible API error envelope with an error code, message,
  and request ID while retaining legacy `detail` values. Validation failures
  use a stable field-location shape; unexpected failures are audit-recorded and
  return a generic response rather than exception text.
- Added first-party idempotency keys to site creation so retried browser
  requests return the original project rather than creating duplicates.
- Persisted project-creation idempotency identity on the job row with a unique
  per-user constraint, closing the reservation-to-job crash gap and protecting
  concurrent retries. Generation still uses in-process tasks; a durable worker
  queue is required to recover generation after process loss.
- Made public order idempotency durable on the order row with a unique
  per-site key and request fingerprint, so a single insert commits order data
  and retry identity together. Legacy reservation records remain readable while
  existing keys age out; retries with changed payloads conflict.
- Added validated `limit` and `offset` pagination to authenticated project
  listings while preserving their array response for existing clients. The API
  returns total and next-offset headers, and bounds recent event loading to
  eight records per listed project.
- Restricted public upload URLs to sanitized image filenames and explicit image
  MIME types with `nosniff` and same-site resource policy headers. Legacy PDFs
  and arbitrary files left in upload directories are no longer served there.
- Extracted shared image validation and bounded PDF parsing into `app/uploads.py`
  so web and Telegram ingestion use the same upload policy.
- Limited each account to 20 web uploads per hour in one process. This is an
  immediate abuse control; shared Redis enforcement is still required for
  multi-worker deployments.
- Added bilingual keyboard skip links and a focusable primary-content landmark
  to the standard portfolio, storefront, and exported storefront templates. This
  is a baseline improvement, not a WCAG conformance claim.
- Escaped order data before rendering the generated merchant operations table,
  and added a keyboard skip link and primary-content landmark to that portal.
- Admin project status labels are inserted as text nodes instead of HTML, and
  both dashboard copies carry the same rendering change.
- Escaped SQL result column names in the optional tenant reporting view; row
  values were already escaped before display.
- Hardened the opt-in tenant reporting query boundary: SQL length and result
  rows are bounded, SQLite execution has a short instruction-time budget, and
  the SQLite authorizer permits reads only from allow-listed tables (including
  when queries use joins or nested selects). This remains a prototype console,
  not a production reporting API, and is disabled by default.
- Added a strict request contract and a 1 MB content bound to the disabled
  tenant file editor. This limits accidental resource use; arbitrary code edits
  still require artifact versioning, validation, review, and a safe publish path.
- Artifact filenames now reject raw empty and dot path components before path
  normalization, preventing alternate spellings from bypassing canonical path
  checks while retaining legitimate generated dotfiles such as `.env.example`.
- Expanded the local/CI credential-pattern scan to cover tracked and non-ignored
  untracked text files; the current workspace scan found no high-confidence
  matches. This does not scan Git history, ignored environment files, or binary
  assets and is not evidence that provider secrets have been rotated.
- The administrator workflow-decision endpoint now requires an explicit
  `approve` or `reject`, rejects extra fields, and cannot interpret an empty
  request as approval to start generation or delivery.
- Marketing-draft decisions now require a strict positive ID and explicit
  `approve` or `reject`; only pending drafts can transition, and owner actions
  are written to the audit trail.
- Store settings now use a bounded, extra-forbidden patch contract; partial
  updates preserve omitted values, while domain, color, and logo URL inputs are
  validated before the public storefront is rebuilt.
- Admin post and agent-proposal decisions no longer default to approval. Their
  request bodies are explicit allow-listed choices, and proposals can only be
  approved/rejected while pending or rolled back after a prompt was applied.
- Site refinement requests now bound prompt and extracted-document sizes,
  reject unknown fields, and limit attached asset references to HTTPS or the
  sanitized local upload path before any LLM call.
- Marketing draft requests bound goal, audience, and theme text, restrict social
  platforms to the dashboard's supported values, and run prompt guardrails before
  sending merchant-provided text to an LLM.
- The visual site editor now accepts only its bounded text/color/logo fields and
  strict boolean section toggles; unknown markup fields cannot be silently
  ignored or interpreted by downstream template code.
- Escaped dynamic fields from static security-review reports before the
  dashboard inserts checklist, passed-rule, and finding details into HTML.
- Routed API-provided GitHub, Vercel, and generated-site links through the
  dashboard URL policy and isolated newly opened tabs from their source page.
- Normalized product prices and IDs before HTML rendering or delete-action
  insertion in the merchant product table; invalid IDs are omitted.
- Ignore malformed non-object entries in the product API array so one bad record
  cannot abort rendering the entire merchant catalog.
- Check product-list HTTP status and response shape; display a fixed error state
  rather than confusing request failures with an empty catalog or interpolating
  exception text into HTML.
- Validate merchant catalog input with field/price bounds and persist image URLs
  only when they use HTTPS or the sanitized local-upload path.
- Escape generated storefront catalog text before HTML insertion and validate
  product IDs/prices at the render boundary to block stored markup injection.
- Apply the same catalog escaping, safe-image URL policy, and numeric validation
  to enterprise-generated product cards, category pills, and cart entries.
- Reduced generated Express parser limits to 256 KiB JSON and 64 KiB URL-encoded
  bodies, disabled nested form parsing, and capped URL-encoded parameters at
  100. Generated security tests reject oversized JSON; edge or gateway limits
  should also be configured in production.
- Removed fabricated enterprise-store reviews and ratings from new exports; the
  storefront now shows an explicit empty state until verified feedback exists.
- Disabled public review submissions in generated projects until purchase
  verification and moderation are implemented.
- Removed fabricated enterprise-store promotions and disabled promo validation
  until server-side checkout applies a validated discount to the final order.
- Disabled generated newsletter collection until explicit consent, unsubscribe,
  and actual email delivery are implemented; storefront copy no longer claims
  messages or discounts are sent.
- Protected generated order listing and dashboard summary APIs with both
  authentication and administrator-role middleware. The generated admin portal
  verifies the server-side session role before revealing customer order data,
  submits credentials only to the login endpoint, and uses the HttpOnly session
  cookie without persisting passwords or tokens in browser storage. Admin users
  still require deliberate provisioning after export; generated registration
  creates customer accounts only.
- Added tighter per-process login and registration throttles to generated stores
  and expire old limiter entries to avoid unbounded stale-key growth. These
  controls supplement the generated API-wide limit only; production deployments
  with multiple workers still require shared Redis-backed rate limiting. Proxy
  trust is now explicit and defaults to zero; forwarded addresses must not be
  trusted unless direct access is blocked and the proxy hop count is verified.
- Connected generated account input validation to both authentication routes.
  Registration now bounds names, emails, phone fields, and passwords (12+ chars,
  at most bcrypt's 72 UTF-8-byte input limit); login validates types and bounds,
  and stored email addresses are normalized to lowercase. Generated security
  tests cover malformed auth requests.
- Disabled generated verification and password-reset email stubs until a real
  delivery provider is configured. They return an explicit unavailable error
  and never write account addresses or recovery tokens to application logs.
- Constrained generated order updates to explicit forward fulfillment states;
  invalid IDs, unknown states, and illegal transitions are rejected, and this
  endpoint cannot alter payment state or mark an order paid.
- Bounded generated checkout inputs, required catalog product IDs and strict
  integer quantities, rejected duplicate/oversized carts, and recomputed totals
  from finite server catalog prices using integer cents. Customer fields are
  length- and format-checked before an order is stored; this remains an order
  request workflow, not a payment processor.
- Connected generated checkout idempotency end to end: the client retains a key
  for same-payload retries, the server hashes and stores the key with a stable
  customer/cart-intent fingerprint, replays return the original order even if
  catalog prices later change, and key reuse with changed contents conflicts.
  Multi-worker deployments still need a durable unique constraint and
  transactional storage to make this concurrency-safe.
- Hardened generated admin product creation with field allow-listing, bounded
  text, finite two-decimal non-negative prices, HTTPS-only image URLs, and
  server-assigned IDs. Generated products start without fabricated ratings or
  stock claims; image-host validation and transactional inventory remain open.
- Apply the same catalog escaping, safe-image URL policy, and numeric validation
  to enterprise-generated product cards, category pills, and cart entries.

## Required before any public deployment

1. Rotate every credential that was ever committed, deployed, logged, or
   entered into the historical dashboard: Telegram, LLM, Turso, GitHub, Vercel,
   payment, webhook, and administrator secrets.
2. Set a new high-entropy `AUTH_SECRET_KEY` and a unique `ADMIN_PASSWORD` in
   the deployment secret manager. Do not put their values in tracked files.
3. Set `PUBLIC_URL` to the exact HTTPS public origin. Add any additional
   first-party origins to `TRUSTED_ORIGINS`.
4. Keep all `ENABLE_*` prototype-risk flags at `0`. Enabling one is not an
   approval to expose it publicly; it requires the secure replacement described
   in the enterprise remediation plan.
5. Put the historic public deployment into maintenance/read-only mode until
   the rotated configuration and a deployment review are complete.

## Not completed or represented as production-ready

- OAuth/OIDC, MFA, durable shared rate limiting, and full audit logging.
- PostgreSQL migrations, database-enforced row-level security, encrypted
  per-tenant secrets, malware scanning, signed object URLs, and retention jobs.
- Real payment gateway adapters and verified webhooks.
- A durable queue/workflow engine, observability/SLOs, infrastructure as code,
  CI/CD security gates, disaster recovery, or multi-region availability.
- Componentized accessible dashboard, CSP nonce rollout, and verified generated
  application builds.

The detailed sequencing and architectural target remain in
[ENTERPRISE_REMEDIATION_PLAN.md](ENTERPRISE_REMEDIATION_PLAN.md).
