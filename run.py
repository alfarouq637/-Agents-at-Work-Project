"""AutoCorp Runner: Launch local development & evaluation server in 1 second.
"""
import os
import sys
from pathlib import Path

# Force UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

import uvicorn
from app.db import init

if __name__ == "__main__":
    print("=" * 65)
    print("⚡ AutoCorp — Autonomous AI Agency for Egyptian SMEs")
    print("=" * 65)
    print("🌐 Dashboard URL:    http://localhost:8000")
    print("👑 Admin Password:   AlfarouqIbrahim")
    print("🤖 Telegram Bot:     t.me/autocorp_Alfarouq_Ibrahim_bot")
    print("📡 Subdomain Mode:   http://{id}.localhost:8000")
    print("=" * 65)
    
    # Initialize database
    try:
        init()
        print("✅ Database initialized successfully (Turso / SQLite).")
    except Exception as e:
        print(f"⚠️ Database Notice: {e}")
        
    print("\nStarting local server on http://127.0.0.1:8000...\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
