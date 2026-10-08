# ⚡ AutoCorp — Autonomous AI Agency for Egyptian SMEs

[![Status](https://img.shields.io/badge/Status-security%20remediation%20in%20progress-orange?style=for-the-badge&logo=shield)](docs/ENTERPRISE_REMEDIATION_PLAN.md)
[![Telegram Bot](https://img.shields.io/badge/Telegram%20Bot-@autocorp__Alfarouq__Ibrahim__bot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/autocorp_Alfarouq_Ibrahim_bot)
[![Hackathon](https://img.shields.io/badge/Agents%20at%20Work-BrainsMingle%20%C3%97%20Wesam.ai-blue)](https://ai.untap.us/programs/aaw-1st-edition)
[![Target](https://img.shields.io/badge/Target-Egyptian%20SMEs-gold)](#-measured-business-impact)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20prototype%20%7C%20SQLite%20%7C%20Turso-teal)](https://github.com/alfarouq637/-Agents-at-Work-Project)

> **Deployment notice:** do not treat any historical hosted URL or Telegram bot
> as production-ready until credential rotation, deployment review, and the
> Phase 0 exit criteria have been completed.

> **AutoCorp** is a FastAPI prototype for Egyptian SMEs. It accepts site briefs,
> produces responsive Arabic-first drafts, and is being evolved into a governed
> multi-tenant platform. Its generated-project and security-review outputs are
> development artifacts, not production or compliance attestations.

> **Current status:** this is a prototype undergoing security remediation. It
> must not be represented as an enterprise production service, payment
> processor, independently verified OWASP implementation, or highly available
> platform. The scoped remediation work is tracked in
> [docs/ENTERPRISE_REMEDIATION_PLAN.md](docs/ENTERPRISE_REMEDIATION_PLAN.md).

---

## ⏱️ Quick Access & Live Links

- 📋 **Architecture and remediation plan**: [docs/ENTERPRISE_REMEDIATION_PLAN.md](docs/ENTERPRISE_REMEDIATION_PLAN.md)
- 👑 **Admin Supervisor Access**: configure a unique `ADMIN_PASSWORD` outside version control; it is never documented or displayed by the application.
- 📡 **Subdomain Routing**: `http://{id}.localhost:8000/` or `http://{slug}.localhost:8000/`
- 🛡️ **Security-audit endpoint**: prototype static analysis only; it is not OWASP certification.
- 🗄️ **Tenant Database API**: `GET /api/sites/{id}/database` & `GET /api/sites/{id}/database/download`

---

## ⏱️ Local 5-Minute Quickstart

Run AutoCorp locally in under 3 minutes with zero extra dependencies:

```bash
# 1. Clone the repository
git clone https://github.com/alfarouq637/-Agents-at-Work-Project.git
cd -Agents-at-Work-Project

# 2. Install the reviewed, hash-verified runtime dependency set
pip install --require-hashes -r requirements.lock

# 3. Configure environment variables (copy example and add your keys)
cp .env.example .env

# 4. Launch the agency platform
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

For the regression suite, install the separately locked test set with
`pip install --require-hashes -r requirements-dev.lock`, then run `pytest -q`.
Regenerate either lock only through reviewed dependency updates using
`pip-compile --strip-extras --generate-hashes --output-file requirements.lock requirements.txt`
or `pip-compile --strip-extras --generate-hashes --output-file requirements-dev.lock requirements-dev.in`.

---

## 📈 Measured Business Impact for Egyptian SMEs

AutoCorp directly addresses the four hackathon judging criteria:

| Hackathon Criterion | Measured Impact in AutoCorp |
| :--- | :--- |
| **1. Prototype capability** | Authenticated users can create a brief, manage a catalog, and receive a template-driven responsive site draft. |
| **2. Current safety posture** | Sessions, ownership checks, uploads, audit events, order pricing, and Telegram webhooks have targeted regression coverage. |
| **3. Remaining delivery work** | Durable workers, PostgreSQL/RLS, verified deployments, accessibility review, and operational observability remain roadmap work. |
| **4. Payments** | Orders are requests pending merchant confirmation. No live provider integration or payment processing claim is made. |

---

## 🏛️ System Architecture Overview

```
                               ┌────────────────────────────────┐
                               │           AutoCorp             │
                               │     CEO & Executive Office     │
                               └───────────────┬────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               │                               │                               │
       ┌───────┴───────┐               ┌───────┴───────┐               ┌───────┴───────┐
       │     Sales     │               │  Engineering  │               │   Security    │
       │  - Prospector │               │  - Architect  │               │ - Cybersecurity│
       │  - Scribe     │               │  - Frontend   │               │   Reviewer    │
       │  - Deal Closer│               │  - Backend    │               │ - SAST Engine │
       └───────────────┘               └───────┬───────┘               └───────┬───────┘
                                               │                               │
                                       ┌───────┴───────────────────────────────┴───────┐
                                       │       4 Metaprompting & Governance Layer       │
                                       │  1. CoT Planning (<thinking>)                 │
                                       │  2. Constraint Guardrails (Atomic UI, Drizzle)│
                                       │  3. OWASP Top 10 Security Prompt              │
                                       │  4. Automated Self-Correction Loop & Unit Test│
                                       └───────────────────────┬───────────────────────┘
                                                               │
                                       ┌───────────────────────┴───────────────────────┐
                                       │            Delivered Store Artifacts          │
                                       │  - Responsive AR/EN Client (Tailwind + ARIA)  │
                                       │  - Express 5 Modular Backend (src/modules/*)  │
                                       │  - Drizzle ORM Relational Models & SQLite DB  │
                                       │  - HttpOnly Secure Cookie JWT Authentication  │
                                       │  - Jest & Supertest Automated Test Suite      │
                                       └───────────────────────────────────────────────┘
```

---

## 🚀 Key Innovations & Features

### 1. 🛡️ Cybersecurity Reviewer Agent & SAST Engine (OWASP Top 10)
- **Dedicated Cybersecurity Reviewer Agent**: Audits generated code before deployment against the OWASP Top 10 standards:
  - `A01: Broken Access Control`: Verifies role guards (`auth.middleware.js`, `admin.middleware.js`).
  - `A02: Cryptographic Failures`: Deep regex scanner detecting leaked API keys, tokens, or hardcoded secrets.
  - `A03: Injection`: Strictly blocks unparameterized SQL concatenation; mandates Drizzle ORM.
  - `A04: Insecure Design`: Enforces rate limiters and payload schemas against DDoS and brute force.
  - `A05: Security Misconfiguration`: Enforces Helmet.js headers and strict CORS origin checks.
  - `A06: Vulnerable Dependencies`: Inspects npm dependency tree for hardened libraries.
  - `A07: Authentication Failures`: Eliminates XSS token theft by storing JWTs exclusively in **HttpOnly, Secure Cookies**.
  - `A08: Software & Data Integrity`: Verifies external CDNs and assets.
  - `A09: Logging & Monitoring`: Structured request logging via Morgan and tenant audit log.
  - `A10: SSRF Prevention`: Enforces isolated tenant scope with zero arbitrary outbound URL fetchers.
- **Automated static review**: a lightweight heuristic scans selected generated-file patterns. It is a development signal, not a penetration test, dependency audit, OWASP certification, or deployment approval.
- **Current platform controls**: remediation has added revocable HttpOnly sessions, Argon2id local passwords, ownership checks, constrained uploads, audit records, origin controls, and targeted regression tests.

### 2. 🗄️ Multi-Tenant Database Engine & Drizzle ORM Abstraction
- **Current tenancy boundary**: tenants share the prototype SQLite/Turso schema and are separated by authenticated ownership checks and `job_id` predicates. This is not physical isolation or database-enforced RLS.
  - Downloadable starter artifacts such as `schema.sql` and `database.json`.
  - Optional local `database.sqlite` development output; it is not a serverless persistence mechanism.
  - Prototype metadata tables in the shared control-plane database.
- **Drizzle ORM Relational Schema**:
  - `src/config/drizzle.js`: Type-safe SQLite connection via `better-sqlite3`.
  - `src/models/drizzle.schema.js`: Complete schema definitions for `users`, `categories`, `products`, `orders`, `promoCodes`, `reviews`, and `store_settings`.
- **Tenant database surfaces**: the SQL console and arbitrary file editor are disabled by default pending PostgreSQL migrations, RLS, versioned artifacts, and reviewed publishing workflows.

### 3. 🧠 4 Advanced Metaprompting Layers with Self-Correction
AutoCorp can generate template-driven drafts and run selected static checks; it does not guarantee factual correctness, accessibility conformance, security, or autonomous self-correction.
1. **Planning direction**: generation uses constrained templates and application guardrails.
2. **Design direction**: a component design system and localization are target architecture work, not enforced output guarantees.
3. **Security direction**: generated artifacts receive limited static review and must later pass independent runtime and deployment checks.
4. **Improvement direction**: production self-improvement must be offline-evaluated, approval-gated, canaried, and reversible.

### 4. 🎨 Front-End Excellence Layer (Atomic Components & RTL)
- **Current output**: generated templates are Arabic-first, responsive drafts with basic viewport and safety validation.
- **Not yet certified**: the legacy dashboard still needs componentization, WCAG 2.2 AA review, performance budgets, and device-matrix testing.

### 5. 📦 Enterprise Node.js / Express 5 Modular Architecture
Generated projects follow a clean MVC modular architecture:
```
Store-Backend/
│
├── src/
│   ├── config/
│   │   ├── database.js          # In-memory / JSON / SQLite data store
│   │   ├── drizzle.js           # Drizzle ORM connection
│   │   ├── schema.sql           # SQL DDL & initial catalog seeds
│   │   └── env.js               # Validated environment configuration
│   ├── models/
│   │   ├── drizzle.schema.js    # Drizzle ORM Relational Schema
│   │   └── index.js             # Model associations
│   ├── modules/                 # auth, products, categories, orders, cart,
│   │                            # reviews, discounts, promoCodes, dashboard
│   ├── middlewares/             # auth (HttpOnly cookies), admin, rateLimiter, helmet
│   ├── utils/                   # response envelopes, ApiError, jwt, pagination
│   └── app.js                   # Express 5 app with Helmet, CORS, Morgan
│
├── public/
│   ├── index.html               # Bilingual AR/EN Atomic SPA Storefront
│   └── admin.html               # Operations Admin Portal
├── tests/
│   ├── security.test.js         # OWASP Top 10 Automated Test Suite
│   └── api.test.js              # REST API Endpoint Test Suite
├── database.sqlite              # Physical SQLite 3 tenant database
├── Dockerfile & docker-compose.yml
├── vercel.json & package.json
└── README.md                    # Deployment & API guide
```

### 6. 💳 Payment status

The prototype records an order request from server-side catalog prices and
leaves it `pending_confirmation`. It does not initiate, verify, or settle a
payment. Official provider adapters, signed webhooks, reconciliation, and a
financial ledger are prerequisites for enabling live payments.

### 7. 🪄 Iterative Prompt Refinement & Multimodal Upload
- **Natural Language Refinement (`/api/sites/{id}/refine`)**: Users can update their live store via natural language prompts (e.g. *"غير الثيم للون الأخضر وزود قسم للمشروبات الساخنة"*).
- **Multimodal Document Intake**: Authenticated users can upload bounded PDF and image inputs; document text extraction is intentionally limited.
- **Visual Code & File Editor**: Disabled pending a tenant-isolated, reviewed editing workflow.

### 8. 📢 AI Marketing Automation & Bot Bridging
- **Autonomous Email Campaign Generator**: Drafts consent-based customer email marketing sequences with human-in-the-loop review.
- **Social Media Case Study Publisher**: Drafts factual LinkedIn/Facebook announcements upon project completion.
- **Telegram & WhatsApp Bot Bridge**: per-merchant credentials are disabled until encrypted secret storage, provider verification, consent, and scoped authorization are available.

### 9. 🤖 Dual-Channel Telegram Bot Integration
- **Client Channel**: Clients send text briefs or photos of their products. The `Vision Analyst` parses the image and triggers project execution.
- **Admin Channel**: Password commands are disabled. Approval callbacks are restricted to the configured owner and webhook deliveries are authenticated and deduplicated.

### 10. 👑 Super Admin Governance & Cascading Control
- Super Admin portal allows:
  - Real-time audit of all SME projects and files.
  - Arbitrary tenant code editing and tenant SQL remain disabled by default.
  - Cascading site deletion with confirmation dialog (removes files, database records, order history, and storage).

---

## 🏢 70-Role Agency Roster Hierarchy

AutoCorp employs 70 specialized agent roles across 10 departments:

```
                          ┌──────────────────────────┐
                          │         AutoCorp         │
                          │   CEO / Executive Office │
                          └─────────────┬────────────┘
                                        │
    ┌────────────────┬──────────────────┼─────────────────┬────────────────┐
    │                │                  │                 │                │
┌───┴────┐      ┌────┴────┐        ┌────┴────┐       ┌────┴────┐      ┌────┴────┐
│ Sales  │      │   Web   │        │   QA    │       │  Media  │      │ Finance │
│ Scribe │      │Frontend │        │Cybersec │       │ Copy-   │      │ Payroll │
│ Deals  │      │Backend  │        │Reviewer │       │ writers │      │ Ledger  │
└────────┘      └─────────┘        └─────────┘       └─────────┘      └─────────┘
```

---

## 🛠️ Environment Configuration (`.env`)

AutoCorp works out of the box with local SQLite fallback. To connect cloud databases, live LLMs, and Telegram bots, create your `.env` (or copy `.env.example`):

```env
# Mode (0 = live LLM providers, 1 = mock simulation)
MOCK=0
MOCK_FALLBACK=1

# Database (Turso libSQL Cloud or leave empty for local SQLite fallback)
TURSO_DATABASE_URL=libsql://your-database-name.aws-eu-west-1.turso.io
TURSO_AUTH_TOKEN=your-turso-jwt-auth-token
SQLITE_PATH=corp.db

# LLM Providers (OpenRouter, NVIDIA NIM, Groq, Cerebras, Mistral)
OPENROUTER_API_KEY=your-openrouter-api-key
NVIDIA_API_KEY=your-nvidia-api-key
NVIDIA_MODEL=deepseek-ai/deepseek-v4.1-flash
NVIDIA_VISION_MODEL=meta/llama-3.2-90b-vision-instruct
GROQ_API_KEY=your-groq-api-key

# Admin Credentials
ADMIN_PASSWORD=your_secure_admin_password
AUTH_SECRET_KEY=your-random-session-signing-secret

# Telegram Bot (Optional - for client intake & mobile approvals)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username
```

`AUTH_SECRET_KEY` and `ADMIN_PASSWORD` are mandatory for browser and
administrator authentication. Generate distinct high-entropy values in the
deployment secret manager; the application intentionally fails those flows
closed when they are absent. See [Phase 0 containment status](docs/PHASE0_CONTAINMENT_STATUS.md)
before exposing an environment publicly.

---

## 👨‍💻 Founder & Project Lead

- **Founder & Lead AI Engineer**: **Alfarouq Ibrahim Farouq** (م. الفاروق إبراهيم فاروق)
- **LinkedIn**: [https://www.linkedin.com/in/alfarouq-ibrahim](https://www.linkedin.com/in/alfarouq-ibrahim)
- **GitHub**: [https://github.com/alfarouq637](https://github.com/alfarouq637)
- **Email**: `alfarwqabrahym0@gmail.com`
- **WhatsApp**: `+201013725515`

---

## 🏆 Submission Deliverables Summary

- **Historical demo deployment**: [https://autocorp-ai-websits-builder.vercel.app/](https://autocorp-ai-websits-builder.vercel.app/) — do not treat as a production service; it requires secret rotation and release-gate verification.
- **Historical Telegram bot**: [t.me/autocorp_Alfarouq_Ibrahim_bot](https://t.me/autocorp_Alfarouq_Ibrahim_bot) — rotate its token and configure its signed webhook before use.
- **GitHub Repository**: [https://github.com/alfarouq637/-Agents-at-Work-Project.git](https://github.com/alfarouq637/-Agents-at-Work-Project.git)
- **Security audit route**: prototype static review only; it is not an OWASP certification or a production security attestation.
- **Hackathon Track**: Agents at Work 1st Edition — BrainsMingle × Wesam.ai (untap.us)
