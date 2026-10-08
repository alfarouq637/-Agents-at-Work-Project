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
from app.runtime import runtime_security_status

if __name__ == "__main__":
    tg_bot = os.getenv("TELEGRAM_BOT_USERNAME", "")
    bot_info = f"t.me/{tg_bot}" if tg_bot else "Configure via TELEGRAM_BOT_TOKEN in .env"
    
    print("=" * 65)
    print("⚡ AutoCorp — Autonomous AI Agency for Egyptian SMEs")
    print("=" * 65)
    print("🌐 Dashboard URL:    http://localhost:8000")
    print("👑 Admin access:     configured through ADMIN_PASSWORD (never printed)")
    print(f"🤖 Telegram Bot:     {bot_info}")
    print("📡 Subdomain Mode:   http://{id}.localhost:8000")
    print("=" * 65)
    
    readiness = runtime_security_status()
    if not readiness["ready"]:
        print("WARNING: Browser/admin authentication is disabled until these settings are configured: " + ", ".join(readiness["missing_required_settings"]))
    if readiness["missing_required_dependencies"]:
        print("WARNING: Required security dependencies are unavailable: " + ", ".join(readiness["missing_required_dependencies"]))
    if readiness["missing_serverless_storage_settings"]:
        print("WARNING: Vercel requires durable Turso storage: " + ", ".join(readiness["missing_serverless_storage_settings"]))
    if readiness["enabled_prototype_features"]:
        print("WARNING: High-risk prototype flags enabled: " + ", ".join(readiness["enabled_prototype_features"]))

    # Initialize database
    try:
        init()
        print("✅ Database initialized successfully (Turso / SQLite).")
    except Exception as e:
        print(f"⚠️ Database Notice: {e}")
        
    print("\nStarting local server on http://127.0.0.1:8000...\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
