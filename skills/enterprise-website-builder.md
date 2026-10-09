---
roles: *
departments: engineering, product, security, design, delivery
tools: calc, fetch_url
---
# AutoCorp Enterprise Web Application Engineering Framework

All AutoCorp agents MUST follow these mandatory security fundamentals, design guidelines, and AI auditing protocols BEFORE generating or modifying any website.

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
   - State factual automated analysis findings only.
4. **Zero-Trust Client Pricing**:
   - NEVER trust client-supplied totals (`total_egp`) or client price calculations.
   - Always calculate prices server-side from authoritative catalog snapshots. Require idempotency keys.
5. **DOM XSS Immunity**:
   - NEVER interpolate raw strings or `${e.message}` directly into `innerHTML`. Every dynamic string MUST be escaped (`esc()`).

## 🧠 Step 1: Deep Learning Security Audit & Autonomous Feedback Loop
1. **Deep Learning Semantic Inspection**:
   - Every generated website MUST pass through the Deep Learning Security Model (`deep_learning_security_audit`).
   - The neural model parses the AST and semantics of client scripts and HTML to detect complex DOM XSS, tab-nabbing, exposed credentials, and insecure sinks (`eval`, `document.write`).
2. **Autonomous Closed-Loop Remediation**:
   - If the Deep Learning Security Model detects vulnerabilities (score < 90/100 or critical/high issues), it generates structured `actionable_feedback`.
   - The feedback is immediately sent back to the `Frontend Developer` agent in an automated loop to self-heal and harden the code until the security threshold is achieved.

## 🛡️ Step 2: Active Security Protection Filters (WAF & Headers)
1. **Input Payload Inspection Filters**:
   - Reject query strings or payloads with `<script>`, `UNION SELECT`, `' OR '1'='1`, `../` path traversal, or null bytes (`%00`).
2. **Defensive Response Header Filters**:
   - Enforce `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-XSS-Protection: 1; mode=block`.
   - Mark all authenticated API responses with `Cache-Control: no-store`.

## 🎨 Step 3: Calm Eye-Friendly Styling, Neon Accents & Universal Usability
1. **Calm, Non-Glare Base Palette with Neon Accents**:
   - Base surfaces MUST be calm, deep, and eye-friendly: dark slates, deep graphite, or soft charcoal (`#0B0F17`, `#0F172A`, `#111827`) avoiding harsh or glaring bright backgrounds.
   - Highlight interfaces with subtle, elegant **neon accent colors**:
     - Neon Cyan (`#00F2FE`), Neon Emerald (`#00F5A0`), Neon Amber (`#FFB800`), Neon Violet (`#A855F7`).
     - Subtle neon glowing borders and button glows (`box-shadow: 0 0 15px rgba(...)`).
2. **Universal Cross-Device Ease of Use**:
   - Mobile-first ergonomic touch targets: all buttons and interactive elements MUST have a minimum height of 44px (`min-h-[44px]`).
   - Sticky bottom quick action bar on mobile for instant WhatsApp communication and cart ordering.
   - High-contrast, crystal-clear Arabic typography with Cairo (`font-cairo`) and Readex Pro (`font-readex`).
   - Responsive layouts tested at 320px, 768px, 1024px, and 1440px breakpoints.

## 🏗️ Step 4: Multi-Tenancy & Egyptian SME Commerce
1. **Tenant Query Scoping**: Every database query MUST bind the tenant ID (`WHERE job_id = ? AND user_id = ?`).
2. **Atomic Multi-Entity Transactions**: Use database transactions for multi-row balance or catalog updates.
3. **Local Payment Flows**: Clear checkout options for Vodafone Cash, InstaPay, Fawry, and Cash on Delivery with pending confirmation status.

## 🧪 Step 5: Verification & CI/CD Security Gates
1. Run automated tests (`pytest`) ensuring 100% pass rate before commit.
2. Run tracked secret scanner (`python scripts/scan_tracked_secrets.py`).
3. Ensure byte-for-byte parity between static dashboard mirrors (`static/` and `api/static/`).
