---
roles: *
departments: engineering, product, security, design, delivery
tools: calc, fetch_url
---
# AutoCorp Enterprise Web Application Engineering Framework

All AutoCorp agents (Developers, Architects, Security Reviewers, Designers) must adhere to this Phase 0 & Phase 1 framework when designing, generating, or modifying web applications.

## Step 1: Security & Session Baseline (Phase 0)
1. **Zero Hardcoded Secrets**:
   - Never embed API keys, secrets, or passwords in code, configs, or templates.
   - Secrets must load from environment variables (`os.getenv()`); fail closed on missing critical secrets.
   - Redact all tokens, credentials, and sensitive configurations from API responses.
2. **Hardened Authentication**:
   - Hash passwords with **Argon2id** (with seamless auto-migration for legacy hashes).
   - Use signed, **HttpOnly**, `SameSite=Lax` (or `Strict`), `Secure` session cookies.
   - Maintain a server-side revocable session registry (`auth_sessions`) so logout instantly invalidates tokens.
   - Support dual-channel extraction: Cookie (`autocorp_session`) with fallback to header (`x-user-token`).
   - Implement login rate limiting/throttling to prevent brute-force attacks.
3. **Upload Boundary & Media Quarantine**:
   - Validate file uploads against size limits (<= 5 MB), extension allow-lists, and binary magic signatures.
   - Decode images, enforce a 20-megapixel ceiling, strip all EXIF metadata, and re-encode before disk persistence.
   - Process PDF briefs transiently in memory; never expose raw documents at public URLs.
4. **Network Perimeter & Defense-in-Depth**:
   - Apply security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
   - Mark API responses with `Cache-Control: no-store`.
   - Validate CORS origins: reject state-changing writes from untrusted cross-origin referrers.
   - Provide a fail-closed `/api/healthz` readiness probe verifying database readiness without exposing secrets.

## Step 2: Architecture & Multi-Tenancy (Phase 1)
1. **Strict Data Schemas**:
   - Define strict Pydantic v2 models for all request payloads and responses with clear validation rules.
   - Use consistent error envelopes: `{"ok": false, "detail": "...", "code": "..."}`.
2. **Tenant Data Isolation**:
   - Enforce tenant ownership at the query level: every database operation must bind the authenticated tenant/job ID (`WHERE job_id = ?`).
   - Index tenant foreign keys (`job_id`, `user_id`) to ensure performant scoped filtering.
   - Execute multi-entity writes inside atomic transactions (SQLite transaction / Turso conditional HTTP batch).

## Step 3: UI/UX & XSS Neutralization (Phase 1)
1. **XSS Immunity**:
   - Never interpolate unescaped variables into HTML strings or `innerHTML`. All dynamic strings must pass through `esc()`.
   - Sanitize URLs: permit only `http:` and `https:`; block `javascript:` and `data:`.
   - Any external anchor tag (`target="_blank"`) must include `rel="noopener noreferrer"`.
   - Arguments passed to inline event handlers must be serialized and escaped (`esc(jsArg(value))`).
2. **Arabic-First SME Design System**:
   - Full RTL support (`dir="rtl" lang="ar"`), styled with Cairo and Readex Pro typography.
   - Mobile-first responsive grid tested at 320px, 768px, 1024px, and 1440px breakpoints.
   - Luxury Egyptian palette: Terracotta `#C0392B`, Gold `#D4AF37`, Deep Slate `#0F172A`.

## Step 4: Egyptian SME Commerce Engine
1. **Anti-Tampering Pricing**:
   - Never trust client-supplied totals (`total_egp`). Calculate order totals server-side using catalog price snapshots.
   - Require idempotency keys on order creation to prevent duplicate charges.
   - Orders remain in `pending_confirmation` until verified by a signed payment gateway webhook.
2. **Egyptian Payment Gateways**:
   - Support local payment methods with clear instructions:
     a) **Vodafone Cash & Wallets**: Display verified merchant wallet number with copy button.
     b) **InstaPay (إنستاباي)**: One-click IPA address transfer.
     c) **Fawry Pay (فوري)**: Generate reference code for kiosk payment.
     d) **Cash on Delivery (الدفع عند الاستلام)**: Confirmed phone/address dispatch.

## Step 5: Truthful Export & Continuous Verification
1. **Clean Project Exports**:
   - Exported starter code must exclude secrets, default passwords, and wildcard CORS.
   - Require explicit production origins and configure containers to run as non-root.
2. **Automated Verification**:
   - All regression and security test suites (`pytest`) must pass 100%.
   - Synchronize static dashboard copies byte-for-byte (`static/` and `api/static/`).
   - Run automated secret scans (`scripts/scan_tracked_secrets.py`) before every deployment.
