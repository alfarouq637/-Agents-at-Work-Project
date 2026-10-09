"""Database layer: Turso libSQL (HTTP) + local SQLite fallback.

When TURSO_DATABASE_URL is set, all queries run over HTTPS against Turso's
/v2/pipeline endpoint — zero native binary dependencies, works on Vercel.
When not set, falls back to local sqlite3 (good for local dev).
"""
import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
LOCAL_DB = os.getenv("SQLITE_PATH", "/tmp/corp.db" if os.getenv("VERCEL", "0") == "1" else "corp.db")

# Normalize libsql:// → https://
_TURSO_HTTP = ""
if TURSO_URL:
    u = TURSO_URL
    if u.startswith("libsql://"):
        u = "https://" + u[len("libsql://"):]
    elif not u.startswith("http"):
        u = "https://" + u
    _TURSO_HTTP = u.rstrip("/")

USE_TURSO = bool(_TURSO_HTTP and TURSO_TOKEN)

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    department TEXT,
    system_prompt TEXT,
    origin TEXT,
    uses INTEGER DEFAULT 0,
    balance REAL DEFAULT 0,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT,
    request TEXT,
    status TEXT,
    plan TEXT,
    result TEXT,
    site_url TEXT,
    price REAL DEFAULT 0,
    cost REAL DEFAULT 0,
    created_at REAL,
    idempotency_key TEXT,
    request_hash TEXT
);
CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL,
    account TEXT,
    delta REAL,
    memo TEXT,
    job_id INTEGER
);
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    from_agent TEXT,
    to_agent TEXT,
    preview TEXT,
    sha256 TEXT,
    ts REAL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    text TEXT,
    status TEXT,
    ts REAL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    ts REAL,
    msg TEXT
);
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT,
    target TEXT,
    content TEXT,
    old TEXT,
    reason TEXT,
    status TEXT,
    ts REAL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT,
    note TEXT,
    ts REAL
);
CREATE TABLE IF NOT EXISTS site_pages (
    job_id INTEGER PRIMARY KEY,
    slug TEXT,
    html TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS site_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    customer_address TEXT,
    items_json TEXT,
    total_egp REAL,
    payment_method TEXT,
    payment_ref TEXT,
    status TEXT DEFAULT 'pending_confirmation',
    created_at REAL,
    idempotency_key TEXT,
    request_hash TEXT
);
CREATE TABLE IF NOT EXISTS site_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    title TEXT,
    price REAL,
    category TEXT,
    description TEXT,
    badge TEXT,
    image_url TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS site_settings (
    job_id INTEGER PRIMARY KEY,
    brand_name TEXT,
    category TEXT,
    custom_domain TEXT,
    color_primary TEXT,
    color_secondary TEXT,
    logo_url TEXT,
    phone TEXT,
    whatsapp TEXT,
    address TEXT,
    vodafone_cash TEXT,
    instapay TEXT,
    fawry_code TEXT,
    cod_enabled INTEGER DEFAULT 1,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'client',
    phone TEXT,
    telegram_id TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    revoked_at REAL
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active_user
    ON user_sessions (user_id, expires_at);
CREATE TABLE IF NOT EXISTS telegram_updates (
    update_id TEXT PRIMARY KEY,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS telegram_messages (
    chat_id TEXT,
    message_id INTEGER,
    status TEXT,
    created_at REAL,
    PRIMARY KEY (chat_id, message_id)
);
CREATE TABLE IF NOT EXISTS telegram_conversations (
    chat_id TEXT PRIMARY KEY,
    stage TEXT,
    pending_brand TEXT,
    pending_niche TEXT,
    last_message TEXT,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS site_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    filename TEXT,
    file_type TEXT,
    content TEXT,
    file_url TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS site_automations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    type TEXT,
    title TEXT,
    content TEXT,
    target_platform TEXT,
    status TEXT DEFAULT 'pending_approval',
    created_at REAL
);
CREATE TABLE IF NOT EXISTS site_bot_configs (
    job_id INTEGER PRIMARY KEY,
    bot_platform TEXT,
    bot_token TEXT,
    bot_name TEXT,
    system_prompt TEXT,
    is_active INTEGER DEFAULT 1,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS tenant_databases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER UNIQUE,
    tenant_id TEXT UNIQUE,
    engine TEXT DEFAULT 'Enterprise SQLite 3 / libSQL Cloud',
    db_filename TEXT DEFAULT 'database.sqlite',
    schema_ddl TEXT,
    tables_catalog TEXT,
    total_tables INTEGER DEFAULT 8,
    total_records INTEGER DEFAULT 0,
    size_bytes INTEGER DEFAULT 0,
    version TEXT DEFAULT '1.0.0',
    last_sync_at REAL,
    status TEXT DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS tenant_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    tenant_id TEXT,
    table_name TEXT,
    record_id TEXT,
    data_json TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS tenant_queries_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    tenant_id TEXT,
    query_sql TEXT,
    rows_affected INTEGER DEFAULT 0,
    execution_ms REAL DEFAULT 0,
    executed_at REAL
);
CREATE TABLE IF NOT EXISTS site_security_audits (
    job_id INTEGER PRIMARY KEY,
    score INTEGER DEFAULT 100,
    grade TEXT DEFAULT 'A+',
    status TEXT DEFAULT 'APPROVED',
    owasp_compliance TEXT,
    findings TEXT,
    passed_rules TEXT,
    checks_passed INTEGER DEFAULT 0,
    checks_total INTEGER DEFAULT 0,
    reviewer_agent TEXT DEFAULT 'Cybersecurity Reviewer',
    audited_at REAL
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at REAL NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id INTEGER,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    outcome TEXT NOT NULL,
    request_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at ON audit_events(occurred_at DESC);
CREATE TABLE IF NOT EXISTS idempotency_records (
    scope TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    job_id INTEGER NOT NULL DEFAULT 0,
    order_id INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    PRIMARY KEY (scope, idempotency_key)
);
"""

# These indexes are applied after additive migrations because older databases
# may not yet have the newer columns when the base schema is first evaluated.
INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_jobs_user_created ON jobs(user_id, created_at DESC)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_user_idempotency ON jobs(user_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_site_files_job_filename ON site_files(job_id, filename)",
    "CREATE INDEX IF NOT EXISTS idx_site_items_job ON site_items(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_site_orders_job_created ON site_orders(job_id, created_at DESC)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_site_orders_idempotency ON site_orders(job_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_site_automations_job ON site_automations(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_tenant_records_job_table ON tenant_records(job_id, table_name)",
    "CREATE INDEX IF NOT EXISTS idx_tenant_queries_job ON tenant_queries_log(job_id, executed_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_posts_job_created ON posts(job_id, ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_idempotency_job ON idempotency_records(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_idempotency_order ON idempotency_records(order_id)",
)

# --------------- Turso HTTP helpers ---------------

_turso_client = None

def _get_turso_client() -> httpx.Client:
    global _turso_client
    if _turso_client is None or _turso_client.is_closed:
        _turso_client = httpx.Client(
            timeout=20.0, 
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=30.0)
        )
    return _turso_client


def _turso_request(statements: List[dict], *, retry: bool = True) -> list:
    """Send SQL to Turso, retrying only when the caller allows it."""
    url = f"{_TURSO_HTTP}/v2/pipeline"
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"requests": statements}
    
    global _turso_client
    last_err = None
    for attempt in range(3 if retry else 1):
        try:
            client = _get_turso_client()
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data.get("results", [])
        except Exception as e:
            last_err = e
            try:
                if _turso_client and not _turso_client.is_closed:
                    _turso_client.close()
            except Exception:
                pass
            _turso_client = None
            time.sleep(0.3)
            
    raise last_err


def _make_stmt_body(sql: str, params: tuple = ()) -> dict:
    """Build a Turso statement dict with typed args."""
    args = []
    for p in params:
        if p is None:
            args.append({"type": "null", "value": None})
        elif isinstance(p, int):
            args.append({"type": "integer", "value": str(p)})
        elif isinstance(p, float):
            args.append({"type": "float", "value": p})
        else:
            args.append({"type": "text", "value": str(p)})
    return {"sql": sql, "args": args}


def _make_stmt(sql: str, params: tuple = ()) -> dict:
    """Build a Turso pipeline statement object."""
    return {"type": "execute", "stmt": _make_stmt_body(sql, params)}


def _rows_to_dicts(result: dict) -> List[Dict[str, Any]]:
    """Convert a Turso result to a list of dicts."""
    resp = result.get("response", {})
    res = resp.get("result", {})
    cols = [c.get("name", f"col{i}") for i, c in enumerate(res.get("cols", []))]
    rows = res.get("rows", [])
    out = []
    for row in rows:
        d = {}
        for i, col in enumerate(cols):
            cell = row[i] if i < len(row) else None
            if isinstance(cell, dict):
                d[col] = cell.get("value")
            else:
                d[col] = cell
        out.append(d)
    return out


# --------------- Local SQLite helpers ---------------

def _sqlite_conn():
    c = sqlite3.connect(LOCAL_DB)
    c.row_factory = sqlite3.Row
    return c


# --------------- Public API (same interface) ---------------

def init():
    """Create all tables. Safe to call multiple times."""
    if USE_TURSO:
        stmts = [s.strip() for s in SCHEMA.split(";") if s.strip()]
        pipeline = [_make_stmt(s) for s in stmts]
        try:
            _turso_request(pipeline)
        except Exception as e:
            print(f"[TURSO INIT] {e}")
        # Safe column additions
        for col_sql in [
            "ALTER TABLE jobs ADD COLUMN user_id INTEGER",
            "ALTER TABLE jobs ADD COLUMN is_paid INTEGER DEFAULT 0",
            "ALTER TABLE jobs ADD COLUMN subscription_plan TEXT DEFAULT 'trial'",
            "ALTER TABLE jobs ADD COLUMN idempotency_key TEXT",
            "ALTER TABLE jobs ADD COLUMN request_hash TEXT",
            "ALTER TABLE idempotency_records ADD COLUMN order_id INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE site_orders ADD COLUMN idempotency_key TEXT",
            "ALTER TABLE site_orders ADD COLUMN request_hash TEXT",
            "ALTER TABLE audit_events ADD COLUMN request_id TEXT",
            "ALTER TABLE site_pages ADD COLUMN slug TEXT"
        ]:
            try:
                _turso_request([_make_stmt(col_sql)])
            except Exception:
                pass
        for index_sql in INDEX_STATEMENTS:
            try:
                _turso_request([_make_stmt(index_sql)])
            except Exception:
                pass
    else:
        c = _sqlite_conn()
        try:
            c.executescript(SCHEMA)
            c.commit()
            for col_sql in [
                "ALTER TABLE jobs ADD COLUMN user_id INTEGER",
                "ALTER TABLE jobs ADD COLUMN is_paid INTEGER DEFAULT 0",
                "ALTER TABLE jobs ADD COLUMN subscription_plan TEXT DEFAULT 'trial'",
                "ALTER TABLE jobs ADD COLUMN idempotency_key TEXT",
                "ALTER TABLE jobs ADD COLUMN request_hash TEXT",
                "ALTER TABLE idempotency_records ADD COLUMN order_id INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE site_orders ADD COLUMN idempotency_key TEXT",
                "ALTER TABLE site_orders ADD COLUMN request_hash TEXT",
                "ALTER TABLE audit_events ADD COLUMN request_id TEXT",
                "ALTER TABLE site_pages ADD COLUMN slug TEXT"
            ]:
                try:
                    c.execute(col_sql)
                    c.commit()
                except Exception:
                    pass
            for index_sql in INDEX_STATEMENTS:
                c.execute(index_sql)
            c.commit()
        finally:
            c.close()


def q(sql: str, args: tuple = ()) -> List[Dict[str, Any]]:
    """SELECT query → list of dicts."""
    if USE_TURSO:
        results = _turso_request([_make_stmt(sql, args)])
        if results:
            if results[0].get("type") == "error":
                err = results[0].get("error", {})
                raise RuntimeError(f"Database query error: {err.get('message', 'unknown error')}")
            return _rows_to_dicts(results[0])
        return []
    else:
        c = _sqlite_conn()
        try:
            return [dict(r) for r in c.execute(sql, args).fetchall()]
        finally:
            c.close()


def one(sql: str, args: tuple = ()) -> Optional[Dict[str, Any]]:
    """SELECT query → single dict or None."""
    rows = q(sql, args)
    return rows[0] if rows else None


def x(sql: str, args: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE → last_insert_rowid (or 0)."""
    if USE_TURSO:
        results = _turso_request([_make_stmt(sql, args)])
        if results:
            if results[0].get("type") == "error":
                err = results[0].get("error", {})
                raise RuntimeError(f"Database execution error: {err.get('message', 'unknown error')}")
            resp = results[0].get("response", {})
            res = resp.get("result", {})
            return res.get("last_insert_rowid", 0) or 0
        return 0
    else:
        c = _sqlite_conn()
        try:
            cur = c.execute(sql, args)
            c.commit()
            return cur.lastrowid or 0
        finally:
            c.close()


def transaction(statements: Sequence[Tuple[str, tuple]]) -> List[int]:
    """Run related writes atomically and return each statement's inserted ID."""
    if not statements:
        return []

    if USE_TURSO:
        # Conditional batch steps ensure later writes stop after a failure.
        steps = [{"stmt": _make_stmt_body("BEGIN IMMEDIATE")}]
        statement_indexes = []
        previous_step = 0
        for sql, args in statements:
            statement_indexes.append(len(steps))
            steps.append({"condition": {"type": "ok", "step": previous_step}, "stmt": _make_stmt_body(sql, args)})
            previous_step = len(steps) - 1

        steps.append({"condition": {"type": "and", "conds": [
            {"type": "ok", "step": step} for step in statement_indexes
        ]}, "stmt": _make_stmt_body("COMMIT")})
        steps.append({"condition": {"type": "or", "conds": [
            {"type": "error", "step": step} for step in statement_indexes
        ]}, "stmt": _make_stmt_body("ROLLBACK")})

        # A lost response after COMMIT is ambiguous; retrying could duplicate writes.
        results = _turso_request([{"type": "batch", "batch": {"steps": steps}}], retry=False)
        if not results or results[0].get("type") != "ok":
            raise RuntimeError("Database transaction failed")
        batch = results[0].get("response", {}).get("result", {})
        errors = batch.get("step_errors", [])
        if any(errors):
            raise RuntimeError("Database transaction failed")
        step_results = batch.get("step_results", [])
        return [
            ((step_results[index] or {}).get("last_insert_rowid", 0) or 0)
            for index in statement_indexes
        ]

    connection = _sqlite_conn()
    try:
        cursor_results = []
        with connection:
            for sql, args in statements:
                cursor_results.append(connection.execute(sql, args).lastrowid or 0)
        return cursor_results
    finally:
        connection.close()


# =========================================================
# Multi-Tenant Database Engine Helpers
# =========================================================
def register_tenant_db(job_id: int, brand: str, schema_sql: str, catalog_tables: list, initial_records: dict = None) -> dict:
    """Registers a dedicated tenant database inside AutoCorp's Master Multi-Tenant engine."""
    tenant_id = f"tenant_db_{job_id}"
    catalog_json = json.dumps(catalog_tables, ensure_ascii=False)
    total_records = 0
    if initial_records:
        for t_name, rows in initial_records.items():
            if isinstance(rows, list):
                total_records += len(rows)
                for idx, r in enumerate(rows):
                    rec_id = str(r.get("id", idx + 1)) if isinstance(r, dict) else str(idx + 1)
                    val_json = json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else json.dumps({"value": r}, ensure_ascii=False)
                    x(
                        "INSERT INTO tenant_records (job_id, tenant_id, table_name, record_id, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (job_id, tenant_id, t_name, rec_id, val_json, time.time(), time.time())
                    )
            elif isinstance(rows, dict):
                total_records += len(rows)
                for k, v in rows.items():
                    x(
                        "INSERT INTO tenant_records (job_id, tenant_id, table_name, record_id, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (job_id, tenant_id, t_name, str(k), json.dumps({"key": k, "value": v}, ensure_ascii=False), time.time(), time.time())
                    )
    
    x("""
        INSERT OR REPLACE INTO tenant_databases 
        (job_id, tenant_id, engine, db_filename, schema_ddl, tables_catalog, total_tables, total_records, size_bytes, version, last_sync_at, status)
        VALUES (?, ?, 'Enterprise SQLite 3 / libSQL Cloud', 'database.sqlite', ?, ?, ?, ?, ?, '1.0.0', ?, 'active')
    """, (
        job_id,
        tenant_id,
        schema_sql,
        catalog_json,
        len(catalog_tables),
        total_records,
        len(schema_sql.encode("utf-8")) + 16384,
        time.time()
    ))
    return {
        "tenant_id": tenant_id,
        "job_id": job_id,
        "total_tables": len(catalog_tables),
        "total_records": total_records
    }


def get_tenant_db(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetches tenant database metadata and status."""
    return one("SELECT * FROM tenant_databases WHERE job_id = ?", (job_id,))


def get_tenant_table_records(job_id: int, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves records from a specific table within the tenant's database virtualization layer."""
    rows = q("SELECT id, table_name, record_id, data_json, created_at FROM tenant_records WHERE job_id = ? AND table_name = ? ORDER BY id ASC LIMIT ?", (job_id, table_name, limit))
    results = []
    for r in rows:
        try:
            d = json.loads(r.get("data_json") or "{}")
            if "id" not in d:
                d["id"] = r.get("record_id")
            results.append(d)
        except Exception:
            pass
    return results


def save_security_audit(job_id: int, audit_data: Dict[str, Any]) -> None:
    """Saves or updates a site's OWASP Top 10 security audit results."""
    x("""
    INSERT OR REPLACE INTO site_security_audits (
        job_id, score, grade, status, owasp_compliance, findings, passed_rules,
        checks_passed, checks_total, reviewer_agent, audited_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        audit_data.get("score", 100),
        audit_data.get("grade", "A+"),
        audit_data.get("status", "APPROVED"),
        json.dumps(audit_data.get("owasp_compliance", {}), ensure_ascii=False),
        json.dumps(audit_data.get("findings", []), ensure_ascii=False),
        json.dumps(audit_data.get("passed_rules", []), ensure_ascii=False),
        audit_data.get("checks_passed", 0),
        audit_data.get("checks_total", 0),
        audit_data.get("reviewer_agent", "Cybersecurity Reviewer"),
        audit_data.get("audited_at", time.time())
    ))


def get_security_audit(job_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a cached OWASP Top 10 security audit for a site."""
    row = one("SELECT * FROM site_security_audits WHERE job_id = ?", (job_id,))
    if not row:
        return None
    try:
        owasp = json.loads(row.get("owasp_compliance") or "{}")
    except Exception:
        owasp = {}
    try:
        findings = json.loads(row.get("findings") or "[]")
    except Exception:
        findings = []
    try:
        passed = json.loads(row.get("passed_rules") or "[]")
    except Exception:
        passed = []

    return {
        "job_id": job_id,
        "score": row.get("score", 100),
        "grade": row.get("grade", "A+"),
        "status": row.get("status", "APPROVED"),
        "owasp_compliance": owasp,
        "findings": findings,
        "passed_rules": passed,
        "checks_passed": row.get("checks_passed", 0),
        "checks_total": row.get("checks_total", 0),
        "reviewer_agent": row.get("reviewer_agent", "Cybersecurity Reviewer"),
        "audited_at": row.get("audited_at", 0)
    }
