"""Vercel Serverless Function entrypoint.

Vercel looks for an `app` object (ASGI/WSGI) in this file.
We import the FastAPI app from app.main and init the DB on cold start.
"""
import os
import sys
from pathlib import Path

# Mark as Vercel environment
os.environ.setdefault("VERCEL", "1")

# Load .env if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Add project root to path so 'app' package is importable
root = str(Path(__file__).resolve().parent.parent)
if root not in sys.path:
    sys.path.insert(0, root)

from app.main import app  # noqa: E402, F401
from app.db import init  # noqa: E402

# Init DB schema on cold start
try:
    init()
except Exception as e:
    print(f"[DB INIT WARNING] {e}")
