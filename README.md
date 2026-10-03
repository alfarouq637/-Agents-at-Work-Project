# ⚡ AutoCorp — Autonomous AI Agency for Egyptian SMEs

> Built for the **Agents at Work** hackathon by BrainsMingle × Wesam.ai

AutoCorp is a **fully autonomous AI agency** that plans, executes, and delivers digital services (websites, media packages, consulting memos) for Egyptian SMEs — using a 70-role AI workforce, multi-provider LLM routing, hash-chained contracts, and human-in-the-loop approvals.

## 🎯 What It Does

1. **Client sends a request** (via dashboard, Telegram photo/text, or webhook)
2. **CEO agent** plans the job, prices it, and hires specialists
3. **Specialist agents** execute tasks with tools (web search, URL fetch, Figma read, calculator)
4. **QA agent** reviews deliverables — can reject and fine the agent
5. **Owner approves** high-stakes decisions (quotes > 2000 EGP, new hires, final delivery)
6. **Marketing agent** drafts a case study post (requires owner approval)
7. **Self-improvement**: QA rejections trigger prompt rewrite proposals with rollback

## 🚀 Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/alfarouq637/-Agents-at-Work-Project.git
cd autocorp

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env: set MOCK=0 and add at least one API key

# 4. Run
uvicorn app.main:app --port 8000 --reload

# 5. Open http://localhost:8000
```

## ☁️ Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Add these environment variables in Vercel Dashboard → Project Settings → Environment Variables:
- `TURSO_DATABASE_URL` — your Turso libSQL URL
- `TURSO_AUTH_TOKEN` — your Turso auth token
- `NVIDIA_API_KEY` — or any other LLM provider key
- `MOCK` → `0`
- `ADMIN_KEY`, `HOOK_KEY`, `CRON_KEY` — security keys

## 🏗️ Architecture

```
Client Request → CEO (plan + price) → Specialist Agents → QA Review → Owner Approval → Delivery
                     ↓                      ↓                ↓
               Agent Factory          Tools (search,      Hash-Chained
               (new roles)           fetch, calc...)     Contracts + Ledger
```

### Key Components

| File | Purpose |
|------|---------|
| `app/db.py` | Turso HTTP API + SQLite fallback |
| `app/llm.py` | Multi-provider LLM router with rotation & cooldown |
| `app/corp.py` | CEO planning, execution, QA, payroll, contracts |
| `app/roles.py` | 70-role roster across 10 departments |
| `app/skills.py` | Markdown skill loader |
| `app/tools.py` | 6 tools: web_search, fetch_url, calc, telegram, webhook, figma_read |
| `app/main.py` | FastAPI app with Vercel-aware execution |
| `api/index.py` | Vercel serverless entrypoint |

### Database: Turso (Serverless SQLite)
- On Vercel: queries run over HTTPS to Turso's `/v2/pipeline` endpoint
- Locally: falls back to local `corp.db` SQLite file
- No native binary dependencies — pure HTTP

### LLM Providers (Free Tiers)
| Provider | Get Key | Notes |
|----------|---------|-------|
| **NVIDIA NIM** | [build.nvidia.com](https://build.nvidia.com/settings/api-keys) | Vision support |
| **Groq** | [console.groq.com](https://console.groq.com/keys) | 30 RPM free |
| **Cerebras** | [cloud.cerebras.ai](https://cloud.cerebras.ai) | Ultra-fast inference |
| **Mistral** | [console.mistral.ai](https://console.mistral.ai) | Vision + free tier |
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) | 25+ free models |

## 📸 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/jobs` | Create a new job |
| `GET` | `/api/jobs` | List recent jobs |
| `GET` | `/api/jobs/{id}` | Job details + events + contracts |
| `POST` | `/api/jobs/{id}/decision` | Approve/reject a job |
| `POST` | `/api/hooks/job` | Inbound webhook (Make/n8n/Zapier) |
| `GET/POST` | `/api/tick` | Trigger self-improvement cycle |
| `GET` | `/api/summary` | Financial dashboard data |
| `GET` | `/api/agents` | Active AI employees |
| `GET` | `/api/roster` | Full 70-role roster |
| `GET` | `/api/providers` | Active LLM providers |
| `POST` | `/api/providers/test` | Test all API keys |
| `GET` | `/api/posts` | Marketing posts |
| `GET` | `/api/proposals` | Self-improvement proposals |

## 📄 License

MIT
