---
roles: *
departments: engineering, product, security, design, delivery
tools: calc, fetch_url
---
# AutoCorp Enterprise Web Application Engineering Framework

All AutoCorp agents (Developers, Architects, Security Reviewers, Designers) MUST follow these non-negotiable security fundamentals and anti-hallucination rules BEFORE generating or modifying any website.

## 🛑 Step 0: Non-Negotiable Security Baseline & Anti-Hallucination Rules
Before writing a single line of code, the agent MUST enforce these guardrails:
1. **Never Hallucinate or Hardcode Secrets**:
   - NEVER invent or embed fake API keys, JWT secrets, passwords, or tokens in code, configs, or frontend scripts.
   - Always load secrets via `os.getenv()`; fail closed (`500` or abort) if a critical secret is missing.
   - Redact all tokens, database credentials, and sensitive configurations from API responses.
2. **Never Hallucinate Payment Gateway Status**:
   - NEVER mark orders as "paid", "completed", or fabricate successful card charge receipts.
   - All orders MUST start in `pending_confirmation`.
   - Never claim a live Paymob/Fawry/InstaPay integration without an authenticated, signed server-side webhook.
3. **Never Hallucinate Security Certifications**:
   - NEVER output claims like "OWASP Top 10 Certified", "Grade A+ Security", or "100% Vulnerability Free".
   - State factual automated static analysis findings only.
4. **Zero-Trust Client Pricing**:
   - NEVER trust client-supplied totals (`total_egp`) or client price calculations.
   - Always calculate prices server-side from authoritative catalog snapshots. Require idempotency keys.
5. **DOM XSS Immunity**:
   - NEVER interpolate raw strings or `${e.message}` directly into `innerHTML`. Every dynamic string MUST be escaped (`esc()`).

## 🛡️ Step 1: Authentication, Sessions & Ingestion (Phase 0)
1. **Hardened Identity**:
   - Passwords hashed with **Argon2id** (auto-migrate legacy scrypt/HMAC hashes on login).
   - Use signed, **HttpOnly**, `SameSite=Lax`, `Secure` session cookies backed by a revocable `auth_sessions` registry.
   - Dual-channel token support: Cookie (`autocorp_session`) + Header (`x-user-token`).
   - Rate limit login attempts to mitigate credential stuffing.
2. **Upload Quarantine**:
   - Strict size limit (<= 5 MB), extension allow-list, and binary **magic byte signature** validation.
   - Decode images, enforce a 20-megapixel ceiling, strip EXIF metadata, and re-encode before saving.
   - Process PDFs transiently in memory; never expose raw uploaded briefs at public URLs.
3. **Defense-in-Depth Headers**:
   - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
   - `Cache-Control: no-store` on API responses. Fail-closed `/api/healthz` readiness probe.

## 🏗️ Step 2: Architecture, Multi-Tenancy & Data Isolation (Phase 1)
1. **Strict Pydantic v2 Schemas**: Validate all inputs and outputs; use standard error envelopes.
2. **Tenant Scoping**: Every database query MUST bind the tenant ID (`WHERE job_id = ? AND user_id = ?`).
3. **Atomic Transactions**: Multi-table updates must run inside atomic transactions (SQLite `BEGIN IMMEDIATE` / Turso HTTP batch).

## 🎨 Step 3: Frontend Security & Egyptian SME Experience (Phase 1)
1. **XSS-Safe DOM Rendering**: Pass all variables through `esc()`. Allow only `http:` / `https:` URLs. External links require `rel="noopener noreferrer"`.
2. **Arabic-First Design System**: Full RTL (`dir="rtl" lang="ar"`), Cairo typography, mobile-first responsive layout (320px to 1440px).
3. **Egyptian SME Commerce**: Local payment flows (Vodafone Cash, InstaPay, Fawry, Cash on Delivery) with clear instructions, copyable wallet/reference numbers, and pending confirmation receipts.

## 🧪 Step 4: Verification & CI/CD Security Gates
1. Run automated tests (`pytest`) ensuring 100% pass rate before commit.
2. Run tracked secret scanner (`python scripts/scan_tracked_secrets.py`).
3. Ensure byte-for-byte parity between static dashboard mirrors (`static/` and `api/static/`).
