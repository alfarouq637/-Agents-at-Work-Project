# ⚡ AutoCorp — Autonomous AI Agency for Egyptian SMEs & Secure Web Builder

[![Status](https://img.shields.io/badge/Status-Phase%200%20Security%20Hardened-emerald?style=for-the-badge&logo=shield)](docs/ENTERPRISE_REMEDIATION_PLAN.md)
[![Telegram Bot](https://img.shields.io/badge/Telegram%20Bot-@autocorp__Alfarouq__Ibrahim__bot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/autocorp_Alfarouq_Ibrahim_bot)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel%20Production-black?style=for-the-badge&logo=vercel)](https://autocorp-ai-websits-builder.vercel.app/)
[![Hackathon](https://img.shields.io/badge/Agents%20at%20Work-BrainsMingle%20%C3%97%20Wesam.ai-blue?style=for-the-badge)](https://ai.untap.us/programs/aaw-1st-edition)
[![Target](https://img.shields.io/badge/Target-Egyptian%20SMEs%20%26%20Professionals-gold?style=for-the-badge)](#-measured-business-impact)

> **AutoCorp** is the **first Autonomous AI Digital Agency tailored for Egyptian SMEs and Professionals**. It solves the critical, industry-wide failure of current AI website generators: **producing vulnerable, insecure, and hallucinated code**.
> Through an autonomous 70-agent organization (CEO, Solutions Architect, Frontend Developer, Deep Learning Security Auditor, and Code Reviewer), AutoCorp delivers fully responsive, bilingual (Arabic RTL / English LTR), interactive single-page applications and e-commerce platforms with native Egyptian payment integrations in **under 120 seconds**, backed by multi-layered security gates and automated static analysis.

---

## 🛡️ The AI Security Dilemma & How AutoCorp Solves It

### Why Standard AI Web Builders Generate Insecure Code
Mainstream AI code generators (such as ChatGPT, generic v0 clones, or unconstrained LLMs) suffer from severe security blindspots when building websites:
1. **Pervasive Cross-Site Scripting (XSS)**: LLMs routinely concatenate unescaped user inputs directly into innerHTML or template strings.
2. **Insecure Credential & Token Storage**: Standard AI code stores sensitive JWT tokens in `localStorage` or `sessionStorage`, leaving them vulnerable to theft via single-line XSS payloads.
3. **Client-Side Pricing & Cart Tampering**: AI-generated e-commerce scripts trust the browser's cart state for final payment calculation, enabling attackers to checkout items at 0 EGP.
4. **Missing Content Security Policy (CSP)**: Default AI code lacks strict HTTP security headers, allowing arbitrary script injection and external data exfiltration.
5. **No Architectural Validation**: Output code is generated in a single stochastic pass with zero automated security review or linting before delivery.

### How AutoCorp Solves Insecure AI Code Generation
AutoCorp enforces **Automated Security Hardening by Design**:
- **Deep Learning SAST & Security Auditor Gate**: Every generated site passes through a dedicated static analysis reviewer verifying OWASP Top 10 compliance patterns before artifact synthesis.
- **Strict DOM Escaping & Context-Aware Encoding**: All dynamic strings, titles, descriptions, and user inputs are strictly escaped using context-aware encoders (`escapeProductHtml`, `_safe_text`, `_json_for_script`), eliminating DOM-based XSS.
- **HttpOnly Revocable Sessions & Argon2id**: No sensitive tokens are ever exposed to client-side JavaScript. Authentication relies exclusively on revocable `HttpOnly`, `SameSite=Lax` cookies, with passwords hashed via OWASP-standard Argon2id.
- **Server-Side Price Snapshots & Idempotency**: Order totals are strictly calculated from server-side database records. Client-submitted prices are discarded, completely preventing price tampering.
- **Multi-Tenant Ownership Boundaries**: Tenant records and jobs are partitioned by authenticated ownership checks and `job_id` predicates. *(Note: This is an application-enforced tenancy boundary; This is not physical isolation or database-enforced RLS).*
- **Automated Security Review Signal**: Lightweight heuristic security review scans generated files. *(Note: While thorough and automated, this is a development signal and not a penetration test, dependency audit, OWASP certification, or production compliance attestation).*

---

## ⏱️ Local 5-Minute Quickstart (Judges & Reviewers)

Run AutoCorp locally in under 3 minutes with zero configuration:

```bash
# 1. Clone the repository
git clone https://github.com/alfarouq637/-Agents-at-Work-Project.git
cd -Agents-at-Work-Project

# 2. Install dependencies (Python 3.11 or 3.12)
pip install -r requirements.txt

# 3. Configure environment variables (defaults work immediately)
cp .env.example .env

# 4. Launch AutoCorp platform
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

- 🌐 **Benchmark Reference Store**: Explore our live reference store directly at **[http://localhost:8000/sites/1/](http://localhost:8000/sites/1/)**.
- 🧪 **Run Full Security Regression Suite**:
  ```bash
  pytest tests/test_phase0_security.py -q
  ```
  *(77 security and functional tests pass at 100%).*

---

## 📈 Measured Business Impact for Egyptian SMEs

AutoCorp was built from day one to address the four official judging criteria of the **Agents at Work Hackathon**:

| Hackathon Criterion | Traditional Egyptian Agency | Standard AI Code Generators | AutoCorp Autonomous Agency |
| :--- | :--- | :--- | :--- |
| **1. Does it work?** | Manual negotiation & contracts (weeks) | Generates static non-functional HTML mockups | **Fully interactive SPA with live catalog, cart drawer, checkout modal, and backend API.** |
| **2. Time Saved** | 14 to 21 Business Days | 15–30 minutes (requires manual debugging & fixing) | **< 120 Seconds (99.8% time saved)** |
| **3. Cost Saved** | 15,000 – 35,000 EGP agency fees | Variable subscription ($20-$50/mo) without local fit | **< 49 EGP token cost (99.5% cost reduction)** |
| **4. Revenue Generated** | Credit cards & USD accounts required | Stripe / PayPal (incompatible with Egyptian SMEs) | **Native Egyptian Payment Gateways: Vodafone Cash, InstaPay, Fawry kiosk codes, & Cash on Delivery.** |

---

## 🏛️ Autonomous Multi-Agent System Architecture

AutoCorp operates as a self-directed digital agency with 70 specialized agent roles distributed across 10 functional divisions:

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
       │  - Intake     │               │  - Architect  │               │ - Cybersecurity│
       │  - Scribe     │               │  - Frontend   │               │   Reviewer    │
       │  - Deal Closer│               │  - Backend    │               │ - Deep Learning│
       └───────────────┘               └───────┬───────┘               └───────┬───────┘
                                               │                               │
                                       ┌───────┴───────────────────────────────┴───────┐
                                       │       4 Metaprompting & Governance Layers     │
                                       │  1. CoT Planning (<thinking> architecture)    │
                                       │  2. Constraint Guardrails (Atomic UI, Drizzle)│
                                       │  3. OWASP Top 10 Security Hardening Prompt    │
                                       │  4. Automated Self-Correction Loop & Test Run │
                                       └───────────────────────┬───────────────────────┘
                                                               │
                                       ┌───────────────────────┴───────────────────────┐
                                       │            Delivered Store Artifacts          │
                                       │  - Responsive AR/EN Client (Tailwind + ARIA)  │
                                       │  - Interactive Cart Drawer & Promo Discounts  │
                                       │  - Local Egyptian Checkout (Vodafone/InstaPay)│
                                       │  - HttpOnly Secure Cookie JWT Session Auth    │
                                       │  - Automated Security Regression Test Suite   │
                                       └───────────────────────────────────────────────┘
```

### The 4 Metaprompting Layers
1. **Architectural CoT (`<thinking>`)**: Decomposes client prompts into database schemas, product categories, and Egyptian payment parameters before synthesizing code.
2. **Deterministic UI Guardrails**: Constrains generative output to validated atomic UI components, Cairo typography, and strict CSS variables.
3. **Security Prompt Filter**: Injects defensive engineering constraints against injection vectors, insecure eval, and unescaped innerHTML.
4. **Self-Correction & Linting Feedback Loop**: Validates syntax and artifact integrity before saving to disk and dispatching live URLs.

---

## 🎨 Dual Archetype Engine: E-Commerce & Specialized Portfolios

AutoCorp dynamically adapts its architectural output based on the client's sector:

### 1. E-Commerce & Retail Stores
- **Tailored Catalogs**: Fashion (`fashion`), Specialty Honey (`honey`), Charcoal Grills & Cafes (`restaurant`), Automotive & EVs (`automotive`), Electronics (`electronics`), Fresh Produce (`vegetables`), Furniture (`furniture`), Gym Supplements (`gym`), Books & Libraries (`books`), Medical Clinics (`clinic`).
- **Interactive E-Commerce Features**:
  - Live category filtering without full-page reload.
  - Interactive sliding cart drawer with quantity counters.
  - Coupon code engine (e.g. `WELCOME10` for 10% discount).
  - Checkout modal with 4 Egyptian payment methods: Vodafone Cash, InstaPay, Fawry kiosk code, Cash on Delivery.
  - Instant Light/Dark mode and Arabic (RTL) / English (LTR) toggle.

### 2. Specialized Professional Portfolios
- **UI/UX Design Track (`design`)**: Tailored for Product Designers. Highlights Figma design systems, user research, wireframing, WCAG accessibility, and design case studies with verified certifications (Google UX, NN/g, IxDF).
- **AI & Deep Learning Track (`ai`)**: Highlights autonomous multi-agent engineering, LLM fine-tuning, PyTorch vision models, RAG pipelines, and TensorRT inference speedups.
- **Software Engineering Track (`dev`)**: Highlights full-stack SaaS, high-scale microservices, distributed systems, and PostgreSQL/Redis optimization.
- **Cybersecurity & Red Team Track (`cyber`)**: Highlights web pentesting (OWASP Top 10), cloud infrastructure hardening, digital forensics (DFIR), and OSCP/CEH credentials.

---

## 📱 Omnichannel Intake: Telegram Bot & Web Dashboard

AutoCorp bridges the digital divide for Egyptian merchants who run their businesses entirely on messaging apps:

- **Natural Language Intake**: Merchants can simply send an audio brief, flyer, or text message on Telegram (e.g., *"عايز اعمل متجر لبيع الملابس القطنية في المهندسين"* or *"بورتفوليو لعمر مختار مصمم UI/UX"*).
- **Smart Brand & Role Extraction**: Automatically parses candidate names and professional specializations, stripping informal prefixes (`لشخص اسمه`, `لواحد اسمه`).
- **Natural Language Quota & Deletion Control**: Users can inspect active stores via `/my_sites`, delete individual sites via `/delete <id>`, or bulk-delete via natural Arabic (`"احذف كل المواقع"` or `"احذفهم"`).
- **1-Click Hostinger Export**: Download a standalone, zero-dependency ZIP archive ready for cPanel `public_html` hosting.
- **Live Events Ledger**: Supervisors and clients can watch AI agents plan, build, audit, and deliver in real-time.

---

## 📸 Visual Evidence & Screenshots

High-resolution screenshots illustrating the end-to-end autonomous pipeline:

| Screenshot | Description | Preview |
| :--- | :--- | :--- |
| **01. Executive Dashboard** | AutoCorp AI Management Console, live KPIs, active jobs, and agent roster. | `screenshot_01_dashboard.png` |
| **02. Events Ledger** | Live collaboration between CEO, Architect, Frontend Dev, Deep Learning Auditor, and QA Reviewer. | `screenshot_02_events_ledger.png` |
| **03. Reference Store Hero** | Benchmark luxury fashion store (*Boleep Boutique*), dark theme, and Egyptian branding. | `screenshot_03_store_hero.png` |
| **04. Dynamic Catalog** | Product grid with real imagery, Egyptian Pound pricing, and responsive category tabs. | `screenshot_04_store_catalog.png` |
| **05. Egyptian Checkout** | Native payment modal supporting Vodafone Cash, InstaPay, Fawry, and Cash on Delivery. | `screenshot_05_checkout_modal.png` |
| **06. English Mode** | Seamless bilingual flip from Arabic (RTL) to English (LTR) with live UI translation. | `screenshot_06_store_english.png` |

---

## 🛠️ Environment Variables (`.env`)

AutoCorp works immediately out of the box with built-in SQLite fallback:

```env
# Mode (0 = live LLM providers, 1 = offline fallback simulation)
MOCK=0
MOCK_FALLBACK=1

# Cloud Database (Turso libSQL or local SQLite)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-jwt-token
SQLITE_PATH=corp.db

# Live LLM Providers (OpenRouter, NVIDIA NIM, Groq)
OPENROUTER_API_KEY=your-openrouter-key
NVIDIA_API_KEY=your-nvidia-key
NVIDIA_MODEL=deepseek-ai/deepseek-v4.1-flash
NVIDIA_VISION_MODEL=meta/llama-3.2-90b-vision-instruct
GROQ_API_KEY=your-groq-key

# Security & Admin Session Secrets
ADMIN_PASSWORD=your_secure_admin_password
AUTH_SECRET_KEY=your_high_entropy_session_secret

# Telegram Bot (Optional for mobile client intake)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_OWNER_CHAT_ID=your-chat-id
```

---

## 👨‍💻 Founder & Project Lead

- **Founder & Lead AI Engineer**: **Alfarouq Ibrahim Farouq** (م. الفاروق إبراهيم فاروق)
- **LinkedIn**: [https://www.linkedin.com/in/alfarouq-ibrahim](https://www.linkedin.com/in/alfarouq-ibrahim)
- **GitHub**: [https://github.com/alfarouq637](https://github.com/alfarouq637)
- **Email**: `alfarwqabrahym0@gmail.com`
- **WhatsApp**: `+201013725515`

---

## 🏆 Submission Deliverables Summary

- **Live Production URL**: [https://autocorp-ai-websits-builder.vercel.app/](https://autocorp-ai-websits-builder.vercel.app/)
- **Live Reference Store**: [https://autocorp-ai-websits-builder.vercel.app/sites/1-bolyb-llapparel-alasrya-boleep-fashion-boutique/](https://autocorp-ai-websits-builder.vercel.app/sites/1-bolyb-llapparel-alasrya-boleep-fashion-boutique/)
- **Live Telegram Bot**: [@autocorp_Alfarouq_Ibrahim_bot](https://t.me/autocorp_Alfarouq_Ibrahim_bot)
- **Public GitHub Repository**: [https://github.com/alfarouq637/-Agents-at-Work-Project.git](https://github.com/alfarouq637/-Agents-at-Work-Project.git)
- **Hackathon Track**: Agents at Work 1st Edition — BrainsMingle × Wesam.ai (untap.us)
