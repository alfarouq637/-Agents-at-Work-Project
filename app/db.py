"""Database layer: Turso libSQL (HTTP) + local SQLite fallback.

When TURSO_DATABASE_URL is set, all queries run over HTTPS against Turso's
/v2/pipeline endpoint — zero native binary dependencies, works on Vercel.
When not set, falls back to local sqlite3 (good for local dev).
"""
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

import httpx

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
LOCAL_DB = os.getenv("SQLITE_PATH", "corp.db")

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
    created_at REAL
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
    html TEXT,
    created_at REAL
);
"""

# --------------- Turso HTTP helpers ---------------

def _turso_request(statements: List[dict]) -> list:
    """Send a pipeline of SQL statements to Turso via /v2/pipeline."""
    url = f"{_TURSO_HTTP}/v2/pipeline"
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"requests": statements}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
    data = r.json()
    return data.get("results", [])


def _make_stmt(sql: str, params: tuple = ()) -> dict:
    """Build a Turso pipeline statement object."""
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
    return {"type": "execute", "stmt": {"sql": sql, "args": args}}


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
    else:
        c = _sqlite_conn()
        try:
            c.executescript(SCHEMA)
            c.commit()
        finally:
            c.close()


def q(sql: str, args: tuple = ()) -> List[Dict[str, Any]]:
    """SELECT query → list of dicts."""
    if USE_TURSO:
        results = _turso_request([_make_stmt(sql, args)])
        if results:
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
