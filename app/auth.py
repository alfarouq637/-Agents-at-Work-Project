"""Authentication & Authorization module for AutoCorp.

Supports:
- Client registration & login
- Admin authentication
- Token issuance and verification
- Per-user store limit enforcement (max 2 sites per client)
- Ownership verification for site settings and exports
"""
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional, Dict, Any
from . import db

import base64
import urllib.parse

try:
    from argon2 import PasswordHasher
    from argon2.low_level import Type
except ImportError:  # pragma: no cover - exercised by deployment readiness.
    PasswordHasher = None
    Type = None

MAX_SITES_PER_CLIENT = 2
TOKEN_TTL_SECONDS = 30 * 86400
# OWASP's current Argon2id baseline: 19 MiB, two passes, one lane. These
# values must be benchmarked again before raising costs on the production tier.
_PASSWORD_HASHER = (
    PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1,
                   hash_len=32, salt_len=16, type=Type.ID)
    if PasswordHasher and Type else None
)


def _secret(name: str) -> str:
    """Read a required secret without silently accepting an insecure default."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


def admin_password() -> str:
    """Return the configured admin password; never use a source-code fallback."""
    return _secret("ADMIN_PASSWORD")


def _password_hasher():
    """Return the required Argon2id implementation or fail the login closed."""
    if _PASSWORD_HASHER is None:
        raise RuntimeError("Argon2id password hashing dependency is unavailable")
    return _PASSWORD_HASHER


def hash_password(pwd: str) -> str:
    """Create an Argon2id verifier with a unique library-generated salt."""
    return _password_hasher().hash(pwd.strip())


def verify_password(plain_pwd: str, hashed: str) -> bool:
    """Verify Argon2id, then support one-login migration from legacy hashes."""
    hasher = _password_hasher()
    if str(hashed).startswith("$argon2"):
        try:
            return bool(hasher.verify(hashed, plain_pwd.strip()))
        except Exception:
            return False
    try:
        scheme, n, r, p, salt_hex, digest_hex = hashed.split("$")
        if scheme != "scrypt":
            raise ValueError("unknown password scheme")
        candidate = hashlib.scrypt(
            plain_pwd.strip().encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(digest_hex)),
        ).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        try:
            legacy = hmac.new(
                _secret("AUTH_SECRET_KEY").encode("utf-8"),
                plain_pwd.strip().encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(legacy, hashed)
        except RuntimeError:
            return False


def password_needs_upgrade(hashed: str) -> bool:
    """Upgrade old algorithms and outdated Argon2id parameters after login."""
    if not str(hashed).startswith("$argon2"):
        return True
    try:
        return _password_hasher().check_needs_rehash(hashed)
    except Exception:
        return True


def generate_token(user_id: int, username: str, role: str) -> str:
    """Create a signed session token and persist its revocation record.

    The token remains self-contained for transport, but its random session ID
    is checked against durable storage on every authenticated request.  This
    makes logout and incident response take effect before the token expires.
    """
    issued_at = int(time.time())
    ts = str(issued_at)
    session_id = secrets.token_urlsafe(24)
    # URL-safe base64 encode username so token never contains non-ISO-8859-1 / Arabic characters or colons
    u_b64 = base64.urlsafe_b64encode(str(username).encode("utf-8")).decode("ascii").rstrip("=")
    payload = f"{user_id}:{u_b64}:{role}:{ts}:{session_id}"
    sig = hmac.new(_secret("AUTH_SECRET_KEY").encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    try:
        db.x(
            "INSERT INTO user_sessions (session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, issued_at, issued_at + TOKEN_TTL_SECONDS),
        )
    except Exception as exc:
        # Do not issue a session that cannot subsequently be revoked.
        raise RuntimeError("Session storage is unavailable") from exc
    return f"{payload}:{sig}"


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed, time-limited application session token."""
    if not token:
        return None
    token = urllib.parse.unquote(str(token).strip())
    
    parts = token.split(":")
    if len(parts) != 6:
        return None
    uid_str, u_b64, role, ts_str, session_id, sig = parts
    if not session_id or not all(c.isalnum() or c in "-_" for c in session_id):
        return None
    payload = f"{uid_str}:{u_b64}:{role}:{ts_str}:{session_id}"
    try:
        expected_sig = hmac.new(_secret("AUTH_SECRET_KEY").encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    except RuntimeError:
        return None
    if not hmac.compare_digest(sig, expected_sig):
        return None
        
    try:
        uid = int(uid_str)
        # Decode username safely
        try:
            padded = u_b64 + "=" * (-len(u_b64) % 4)
            username = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        except Exception:
            username = u_b64  # fallback for legacy tokens
            
        if int(ts_str) > time.time() + 300 or time.time() - int(ts_str) > TOKEN_TTL_SECONDS:
            return None
        return {
            "id": uid,
            "username": username,
            "role": role,
            "is_admin": role == "admin",
            "session_id": session_id,
        }
    except Exception:
        return None


def get_active_user(token: str) -> Optional[Dict[str, Any]]:
    """Resolve a signed session against the current account record.

    A signature proves a token was issued; it must not preserve access after a
    user has been deleted or their role has been changed. The synthetic
    administrator session has ID 0 and is backed by the environment-managed
    administrator credential rather than a database row.
    """
    session = decode_token(token)
    if not session:
        return None
    try:
        stored_session = db.one(
            "SELECT session_id FROM user_sessions "
            "WHERE session_id = ? AND user_id = ? AND revoked_at IS NULL AND expires_at >= ?",
            (session["session_id"], session["id"], time.time()),
        )
    except Exception:
        # Authentication must fail closed when revocation state is unavailable.
        return None
    if not stored_session:
        return None

    if session["id"] == 0 and session.get("role") == "admin":
        return session

    current = db.one("SELECT id, username, role FROM users WHERE id = ?", (session["id"],))
    if not current:
        return None
    return {
        "id": current["id"],
        "username": current["username"],
        "role": current.get("role") or "client",
        "is_admin": current.get("role") == "admin",
    }


def revoke_token(token: str) -> bool:
    """Revoke one valid browser/API session without exposing session details."""
    session = decode_token(token)
    if not session:
        return False
    try:
        db.x(
            "UPDATE user_sessions SET revoked_at = ? "
            "WHERE session_id = ? AND user_id = ? AND revoked_at IS NULL",
            (time.time(), session["session_id"], session["id"]),
        )
        return True
    except Exception:
        return False


def register_user(username: str, password: str, phone: str = "") -> Dict[str, Any]:
    """Registers a new client user."""
    _secret("AUTH_SECRET_KEY")
    username = username.strip()
    if len(username) < 3:
        raise ValueError("اسم المستخدم يجب ألا يقل عن 3 أحرف")
    if len(password) < 12 or len(password) > 1024:
        raise ValueError("كلمة المرور يجب ألا تقل عن 12 خانة")
        
    # Check if user already exists
    existing = db.one("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    if existing:
        raise ValueError("اسم المستخدم مسجل بالفعل، يرجى تسجيل الدخول أو اختيار اسم آخر")
        
    hashed = hash_password(password)
    uid = db.x(
        "INSERT INTO users (username, password_hash, role, phone, created_at) VALUES (?, ?, 'client', ?, ?)",
        (username, hashed, phone.strip(), time.time())
    )
    token = generate_token(uid, username, "client")
    return {
        "id": uid,
        "username": username,
        "role": "client",
        "token": token
    }


def login_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticates a user (admin or client)."""
    _secret("AUTH_SECRET_KEY")
    username = username.strip()
    password = password.strip()

    # Database users only. Administrator authentication is isolated in the
    # dedicated admin endpoint and never returns a master credential.
    u = db.one("SELECT id, username, password_hash, role FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    if not u or not verify_password(password, u.get("password_hash", "")):
        raise ValueError("Invalid username or password")

    uid = u["id"]
    role = u.get("role", "client")
    if password_needs_upgrade(u.get("password_hash") or ""):
        db.x("UPDATE users SET password_hash=? WHERE id=?", (hash_password(password), uid))
    return {
        "id": uid,
        "username": u["username"],
        "role": role,
        "token": generate_token(uid, u["username"], role),
        "is_admin": role == "admin",
    }
def check_user_limit(user: Dict[str, Any]) -> None:
    """Checks if the client has reached the 2-store limit. Raises ValueError if exceeded."""
    if not user or user.get("is_admin") or user.get("role") == "admin":
        return  # Admin has no limit
        
    uid = user.get("id")
    if not uid:
        return
        
    # Strictly count stores created by this registered user
    row = db.one("SELECT count(*) as c FROM jobs WHERE user_id = ?", (uid,))
    count = int(row.get("c", 0) or 0) if row else 0
    if count >= MAX_SITES_PER_CLIENT:
        raise ValueError(
            f"عفواً، لقد استنفدت الحد الأقصى المسموح به ({MAX_SITES_PER_CLIENT} مواقع) في باقتك الحالية! يرجى ترقية الحساب لإنشاء مواقع إضافية."
        )


def verify_site_ownership(jid: int, user: Optional[Dict[str, Any]]) -> bool:
    """Returns True if the user is the admin or the owner of the job."""
    if not user:
        return False
    if user.get("is_admin") or user.get("role") == "admin":
        return True
        
    job = db.one("SELECT user_id, client FROM jobs WHERE id = ?", (jid,))
    if not job:
        return False
        
    uid = user.get("id")
    uname = (user.get("username") or "").strip().lower()
    
    if job.get("user_id") is not None and str(job.get("user_id")) == str(uid):
        return True
    job_client = str(job.get("client") or "").strip().lower()
    if uname and (job_client == uname or job_client.startswith(f"tg:{uname}")):
        return True
    return False
