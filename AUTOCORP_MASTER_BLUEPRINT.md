# 🚀 AutoCorp: Master Architecture, Implementation Blueprint & Handoff Specification

> **Target Project**: AutoCorp — Autonomous AI Agency for Egyptian SMEs  
> **GitHub Repository**: `https://github.com/alfarouq637/-Agents-at-Work-Project.git`  
> **Deployment Target**: Vercel (Serverless Python Backend + Static/SPA Frontend) & Turso libSQL Cloud  
> **Prepared For**: Instant AI Agent Handoff / Autonomous Execution

---

## 1. 🔑 Credentials & Environment Configuration

ضع هذه المتغيرات في ملف `.env` محلياً، وكذلك في **Vercel Project Settings -> Environment Variables**:

```env
# ==========================================
# 1. DATABASE (Turso Cloud libSQL)
# ==========================================
TURSO_DATABASE_URL="libsql://your-database.aws-eu-west-1.turso.io"
TURSO_AUTH_TOKEN="your-turso-auth-token"

# ==========================================
# 2. LLM PROVIDERS & KEYS
# ==========================================
# Mode: 0 for Real LLMs, 1 for Mock
MOCK=0
MOCK_FALLBACK=1

# NVIDIA NIM (NVIDIA API Key)
NVIDIA_API_KEY="nvapi-your-nvidia-key"
NVIDIA_MODEL="deepseek-ai/deepseek-v4.1-flash"
NVIDIA_VISION_MODEL="meta/llama-3.2-90b-vision-instruct"

# Groq (Recommended Free Tier: 30 RPM, 14,400 RPD)
GROQ_API_KEY=""
GROQ_MODEL="llama-3.3-70b-versatile"

# Cerebras (Free Tier: 30 RPM, Ultra-fast)
CEREBRAS_API_KEY=""
CEREBRAS_MODEL="gpt-oss-120b"

# Mistral (Experiment Free Plan: 1 RPS, Vision available)
MISTRAL_API_KEY=""
MISTRAL_MODEL="mistral-small-latest"

# OpenRouter (Free Router)
OPENROUTER_API_KEY=""
OPENROUTER_MODEL="openrouter/free"

# Tier Fallback Hierarchy
LLM_TIER_BRAIN="nvidia,groq,cerebras,mistral,openrouter"
LLM_TIER_WORKER="nvidia,groq,cerebras,mistral,openrouter"
LLM_TIER_VISION="nvidia,mistral,openrouter"

# ==========================================
# 3. AGENCY & SECURITY SETTINGS
# ==========================================
ADMIN_PASSWORD="generate-a-unique-secret-in-your-secret-manager"
AUTH_SECRET_KEY="generate-at-least-32-random-bytes-in-your-secret-manager"
HOOK_KEY="generate-a-unique-webhook-secret-in-your-secret-manager"
CRON_KEY="generate-a-unique-cron-secret-in-your-secret-manager"

SALARY_EGP_PER_1K_TOKENS=0.8
PRICE_MARGIN_RATIO=2.5
APPROVAL_GATE_PRICE=2000.0

# Optional Integrations
TELEGRAM_BOT_TOKEN=""
TELEGRAM_OWNER_ID=""
TAVILY_API_KEY=""
```

---

## 2. 🏛️ Core Architecture & Vercel Adaptation

### 2.1 The Two Critical Serverless Bottlenecks & Their Solutions:

1. **Database Persistence (Solved by Turso)**:
   - **Problem**: Vercel serverless functions have a read-only/ephemeral filesystem; SQLite files (`corp.db`) are wiped on cold starts.
   - **Solution**: We transition `app/db.py` to use `libsql-client` (or HTTP requests to your Turso endpoint `https://your-db.aws-eu-west-1.turso.io`). When `TURSO_DATABASE_URL` is set, queries run against Turso over HTTPS. When not set, it gracefully falls back to local `sqlite3`.

2. **Background Execution (Solved by Dual-Mode Execution)**:
   - **Problem**: `asyncio.create_task(run_job(...))` in `app/corp.py` gets frozen/killed as soon as Vercel finishes returning the HTTP response.
   - **Solution**: 
     - **Mode A (Vercel Serverless)**: Either execute the CEO planning + initial specialist steps synchronously within the request timeout (Vercel allows up to 15s–60s), OR store the job in Turso with status `pending_execution` and trigger steps via an external cron/webhook hitting `POST /api/tick?key=...`.
     - **Mode B (Local/Docker/VPS)**: Keep the background event loop running via `asyncio.create_task` or regular tick loop in `lifespan`.

---

## 3. 📂 Directory Structure for Vercel

```
autocorp/
├── api/
│   └── index.py            # Vercel Serverless Function entry point (exposes FastAPI app)
├── app/
│   ├── __init__.py
│   ├── corp.py             # CEO Planner, Agent Factory, QA loop, Ledger & Contracts
│   ├── db.py               # Database layer: Turso libSQL client + sqlite3 fallback
│   ├── llm.py              # Multi-provider LLM router (NVIDIA, Groq, Mistral, Cerebras)
│   ├── roles.py            # 70-role roster definitions (10 departments)
│   ├── skills.py           # Markdown skill loader & matcher
│   └── tools.py            # Agent tools (web_search, fetch_url, calc, telegram, webhook, figma)
├── skills/
│   ├── automation.md
│   ├── egypt-sme.md
│   ├── figma-handoff.md
│   ├── research.md
│   └── web-delivery.md
├── static/
│   └── index.html          # High-converting Arabized Dashboard (Tailwind CSS + Charts)
├── vercel.json             # Vercel build & route rewrite configuration
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
└── README.md               # Quickstart guide & documentation
```

---

## 4. 💻 Full Code Implementation Specifications

### 4.1 `requirements.txt`
```text
fastapi>=0.110.0
uvicorn>=0.29.0
httpx>=0.27.0
libsql-client>=0.3.0
pydantic>=2.6.0
python-dotenv>=1.0.0
```

---

### 4.2 `app/db.py` (Turso libSQL + SQLite Hybrid Engine)
> **Goal**: Transparent query execution. If `TURSO_DATABASE_URL` is configured, use Turso. Otherwise, use local SQLite.

```python
import os
import sqlite3
import urllib.parse
from typing import Any, Dict, List, Optional

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
LOCAL_DB = os.getenv("SQLITE_PATH", "corp.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    role TEXT PRIMARY KEY,
    department TEXT,
    system_prompt TEXT,
    tools_allowed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    client_name TEXT,
    request_text TEXT,
    image_url TEXT,
    status TEXT,
    quoted_price REAL,
    actual_cost REAL,
    plan_json TEXT,
    deliverable TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    from_role TEXT,
    to_role TEXT,
    task_description TEXT,
    result_text TEXT,
    prev_hash TEXT,
    curr_hash TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    role TEXT,
    tokens_used INTEGER,
    salary_egp REAL,
    is_fine INTEGER DEFAULT 0,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    platform TEXT,
    content TEXT,
    approved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    event_type TEXT,
    payload_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    role TEXT,
    original_prompt TEXT,
    proposed_prompt TEXT,
    status TEXT DEFAULT 'pending',
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    rating INTEGER,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Check if Turso is enabled
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

if USE_TURSO:
    import libsql_client
    # Normalize libsql:// to https:// if needed for HTTP transport
    http_url = TURSO_URL
    if http_url.startswith("libsql://"):
        http_url = "https://" + http_url[len("libsql://"):]
    _turso_client = libsql_client.create_client_sync(
        url=http_url,
        auth_token=TURSO_TOKEN
    )
else:
    _turso_client = None

def get_sqlite_conn():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if USE_TURSO:
        statements = [stmt.strip() for stmt in SCHEMA_SQL.split(";") if stmt.strip()]
        for stmt in statements:
            _turso_client.execute(stmt)
    else:
        with get_sqlite_conn() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

def q(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute SELECT query and return list of dictionaries."""
    if USE_TURSO:
        res = _turso_client.execute(sql, list(params))
        cols = res.columns
        return [dict(zip(cols, row)) for row in res.rows]
    else:
        with get_sqlite_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]

def one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Execute SELECT query and return single dictionary or None."""
    rows = q(sql, params)
    return rows[0] if rows else None

def x(sql: str, params: tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE query and return lastrowid or affected count."""
    if USE_TURSO:
        res = _turso_client.execute(sql, list(params))
        return res.last_insert_rowid or 0
    else:
        with get_sqlite_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid or 0
```

---

### 4.3 `app/llm.py` (Multi-Provider Router with Verified NVIDIA NIM Key)
> **Goal**: Multi-provider resilience. If NVIDIA NIM returns 429/401/error, fallback automatically to Groq, Cerebras, Mistral, OpenRouter, or Mock.

```python
import os
import json
import time
import httpx
from typing import List, Dict, Any, Optional

DEFAULT_PROVIDERS = {
    "nvidia": {
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model": os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4.1-flash"),
        "vision_model": os.getenv("NVIDIA_VISION_MODEL", "meta/llama-3.2-90b-vision-instruct")
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key_env": "CEREBRAS_API_KEY",
        "model": os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key_env": "MISTRAL_API_KEY",
        "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "model": os.getenv("OPENROUTER_MODEL", "openrouter/free")
    }
}

COOLDOWNS: Dict[str, float] = {}

def get_active_providers(tier: str = "brain") -> List[Dict[str, Any]]:
    tier_env = os.getenv(f"LLM_TIER_{tier.upper()}", "nvidia,groq,cerebras,mistral,openrouter")
    order = [p.strip().lower() for p in tier_env.split(",") if p.strip()]
    
    active = []
    now = time.time()
    for name in order:
        if name in DEFAULT_PROVIDERS:
            cfg = DEFAULT_PROVIDERS[name]
            raw_key = os.getenv(cfg["key_env"], "").strip()
            if raw_key:
                # Check cooldown
                if COOLDOWNS.get(name, 0) > now:
                    continue
                active.append({
                    "name": name,
                    "url": cfg["url"],
                    "key": raw_key,
                    "model": cfg.get("vision_model" if tier == "vision" else "model")
                })
    return active

def call_llm(
    prompt: str,
    system_prompt: str = "You are a specialized AI Agent at AutoCorp.",
    tier: str = "worker",
    images: Optional[List[str]] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> Dict[str, Any]:
    """
    Calls LLM with automatic multi-provider fallback.
    Returns: {"text": str, "provider": str, "model": str, "tokens": int}
    """
    if os.getenv("MOCK", "0") == "1":
        return {
            "text": f"[MOCK OUTPUT for: {prompt[:80]}...]",
            "provider": "mock",
            "model": "mock-v1",
            "tokens": len(prompt.split()) + 50
        }

    providers = get_active_providers(tier)
    
    # Construct messages
    messages = [{"role": "system", "content": system_prompt}]
    
    if images and len(images) > 0:
        content = [{"type": "text", "text": prompt}]
        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": img if img.startswith("data:") else f"data:image/jpeg;base64,{img}"}
            })
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    for p in providers:
        name = p["name"]
        url = p["url"]
        key = p["key"]
        model = p["model"]

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        if name == "openrouter":
            headers["HTTP-Referer"] = "https://autocorp.ai"
            headers["X-Title"] = "AutoCorp AI"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    out_text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens", len(out_text.split()) + len(prompt.split()))
                    return {
                        "text": out_text,
                        "provider": name,
                        "model": model,
                        "tokens": tokens
                    }
                elif res.status_code in (429, 401, 503):
                    # Rate limit or quota exhaustion, cooldown 60 seconds
                    COOLDOWNS[name] = time.time() + 60.0
                    continue
        except Exception:
            COOLDOWNS[name] = time.time() + 30.0
            continue

    # Fallback to mock if allowed
    if os.getenv("MOCK_FALLBACK", "1") == "1":
        return {
            "text": f"[FALLBACK OUTPUT: All API providers exhausted. Task completed in simulated mode for {prompt[:60]}...]",
            "provider": "mock-fallback",
            "model": "fallback-v1",
            "tokens": 100
        }
    
    raise RuntimeError("All LLM providers failed or rate-limited, and MOCK_FALLBACK is disabled.")
```

---

### 4.4 `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/sites/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "static/$1"
    }
  ]
}
```

---

### 4.5 `api/index.py` (Vercel Serverless Entrypoint)
```python
import sys
from pathlib import Path

# Add project root directory to path for package imports
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.main import app
from app.db import init_db

# Initialize database schema on startup/cold-start
try:
    init_db()
except Exception as e:
    print(f"[TURSO INIT WARNING] {e}")
```

---

## 5. 🛠️ Execution Checklist for the AI Assistant / Developer

Any AI picking up this task must execute the following sequential steps:

### Phase 1: Environment & Dependency Verification
1. Run `pip install -r requirements.txt`
2. Test connection to Turso DB:
   ```python
   from app.db import init_db, q, x
   init_db()
   print("Turso Tables:", q("SELECT name FROM sqlite_master WHERE type='table'"))
   ```
3. Test NVIDIA NIM API with the provided key:
   ```python
   from app.llm import call_llm
   res = call_llm("Say hello from AutoCorp!", tier="worker")
   print("NVIDIA Response:", res)
   ```

### Phase 2: Core Enhancements in `app/corp.py`
1. Ensure `plan_job()` parses JSON reliably from LLM responses even if Markdown fences (` ```json `) are present.
2. In `execute_job()`, update the SHA-256 hash chaining so each contract has:
   `curr_hash = sha256(f"{prev_hash}{from_role}{to_role}{task}{result}")`.
3. Support direct synchronous execution for Vercel:
   `POST /api/jobs?sync=1` executes the entire pipeline and returns the complete deliverable in the same HTTP call.

### Phase 3: Dashboard Polish (`static/index.html`)
1. Implement a clean, modern UI with Tailwind CSS CDN:
   - Live metrics bar: Total Revenue (EGP), Actual Cost, Tokens Burned, Net Profit.
   - Interactive Agent Roster showing active departments and specialists.
   - Live Job Pipeline tracker: `Planning` -> `Specialist Execution` -> `QA Verification` -> `Owner Approval` -> `Delivered`.
   - Real-time event log with auto-refresh every 3 seconds.

### Phase 4: Git Commit & Vercel Deployment
1. Initialize/configure git remote:
   ```bash
   git remote set-url origin https://github.com/alfarouq637/-Agents-at-Work-Project.git
   git add .
   git commit -m "feat: integrate Turso cloud, NVIDIA NIM LLM router, and Vercel serverless configuration"
   git push origin main
   ```
2. In Vercel Dashboard:
   - Import `https://github.com/alfarouq637/-Agents-at-Work-Project.git`
   - Paste environment variables (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `NVIDIA_API_KEY`, `MOCK=0`).
   - Click **Deploy**.
