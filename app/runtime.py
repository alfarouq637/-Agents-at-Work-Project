"""Small runtime configuration and dependency checks.

This module reports readiness without returning secret values. It is intentionally
separate from HTTP routes so local startup and deployment probes use the same
rules.
"""
import os
from typing import Dict, List
from urllib.parse import urlparse


REQUIRED_SECURITY_SETTINGS = ("AUTH_SECRET_KEY", "ADMIN_PASSWORD")
PUBLIC_WEBHOOK_SETTINGS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_SECRET", "PUBLIC_URL")
RISKY_FEATURE_FLAGS = (
    "ENABLE_DIRECT_DEPLOYMENT",
    "ENABLE_TENANT_FILE_EDITOR",
    "ENABLE_TENANT_SQL_CONSOLE",
    "ENABLE_TENANT_BOT_CREDENTIALS",
    "ENABLE_DEMO_PAYMENT_ACTIVATION",
    "ENABLE_AUTOMATED_DEPLOYMENT",
    "ENABLE_OUTBOUND_WEBHOOKS",
)


def missing_security_settings() -> List[str]:
    """Return missing required setting names, never their values."""
    return [name for name in REQUIRED_SECURITY_SETTINGS if not os.getenv(name, "").strip()]


def _argon2_available() -> bool:
    """Check the local password-hashing requirement without exposing details."""
    try:
        from argon2 import PasswordHasher  # noqa: F401
        return True
    except ImportError:
        return False


def missing_serverless_storage_settings() -> List[str]:
    """Require durable storage when this application runs on Vercel."""
    if os.getenv("VERCEL", "0") != "1":
        return []
    return [
        name for name in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN")
        if not os.getenv(name, "").strip()
    ]


def automation_configuration_errors() -> List[str]:
    """Report unsafe opt-in automation combinations without returning values."""
    errors: List[str] = []
    if os.getenv("ENABLE_AUTOMATED_DEPLOYMENT", "0") == "1" and not os.getenv("NETLIFY_TOKEN", "").strip():
        errors.append("ENABLE_AUTOMATED_DEPLOYMENT requires NETLIFY_TOKEN")

    if os.getenv("ENABLE_OUTBOUND_WEBHOOKS", "0") != "1":
        return errors
    if not os.getenv("OUTBOUND_WEBHOOK_SECRET", "").strip():
        errors.append("ENABLE_OUTBOUND_WEBHOOKS requires OUTBOUND_WEBHOOK_SECRET")

    endpoints = []
    for item in os.getenv("OUTBOUND_WEBHOOKS", "").split(";"):
        if "=" in item:
            _name, url = item.split("=", 1)
            endpoints.append(url.strip())
    if not endpoints:
        errors.append("ENABLE_OUTBOUND_WEBHOOKS requires OUTBOUND_WEBHOOKS")
    elif any(urlparse(url).scheme != "https" or not urlparse(url).hostname for url in endpoints):
        errors.append("OUTBOUND_WEBHOOKS must contain HTTPS URLs")
    return errors


def runtime_security_status() -> Dict[str, object]:
    """Provide a secret-free readiness summary for startup and health probes."""
    missing = missing_security_settings()
    missing_dependencies = [] if _argon2_available() else ["argon2-cffi"]
    missing_serverless_storage = missing_serverless_storage_settings()
    automation_errors = automation_configuration_errors()
    enabled_risky_features = [
        name for name in RISKY_FEATURE_FLAGS if os.getenv(name, "0") == "1"
    ]
    return {
        "ready": not missing and not missing_dependencies and not missing_serverless_storage and not automation_errors,
        "missing_required_settings": missing,
        "missing_required_dependencies": missing_dependencies,
        "missing_serverless_storage_settings": missing_serverless_storage,
        "automation_configuration_errors": automation_errors,
        "telegram_webhook_ready": not [
            name for name in PUBLIC_WEBHOOK_SETTINGS if not os.getenv(name, "").strip()
        ],
        "enabled_prototype_features": enabled_risky_features,
    }
