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
import time
from typing import Optional, Dict, Any
from . import db

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "autocorp-secure-token-salt-2026")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
ADMIN_KEY = os.getenv("ADMIN_KEY", "autocorp-admin-secret-2026")
MAX_SITES_PER_CLIENT = 2


def hash_password(pwd: str) -> str:
    """Computes SHA-256 HMAC for password storage."""
    return hmac.new(SECRET_KEY.encode("utf-8"), pwd.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(plain_pwd: str, hashed: str) -> bool:
    """Verifies candidate plain password against stored hash."""
    return hmac.compare_digest(hash_password(plain_pwd), hashed)


def generate_token(user_id: int, username: str, role: str) -> str:
    """Generates a secure stateless token: uid:role:ts:signature."""
    ts = str(int(time.time()))
    payload = f"{user_id}:{username}:{role}:{ts}"
    sig = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a stateless token or checks admin key."""
    if not token:
        return None
    token = token.strip()
    
    # Check if admin master key or password
    if token in (ADMIN_KEY, ADMIN_PASSWORD):
        return {
            "id": 0,
            "username": "admin",
            "role": "admin",
            "is_admin": True
        }
        
    parts = token.split(":")
    if len(parts) != 5:
        return None
    uid_str, username, role, ts_str, sig = parts
    payload = f"{uid_str}:{username}:{role}:{ts_str}"
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
        
    try:
        uid = int(uid_str)
        # Check token expiration (e.g., 30 days)
        if time.time() - int(ts_str) > 30 * 86400:
            return None
        return {
            "id": uid,
            "username": username,
            "role": role,
            "is_admin": (role == "admin")
        }
    except Exception:
        return None


def register_user(username: str, password: str, phone: str = "") -> Dict[str, Any]:
    """Registers a new client user."""
    username = username.strip().lower()
    if len(username) < 3:
        raise ValueError("اسم المستخدم يجب ألا يقل عن 3 أحرف")
    if len(password) < 4:
        raise ValueError("كلمة المرور يجب ألا تقل عن 4 خانات")
        
    # Check if user already exists
    existing = db.one("SELECT id FROM users WHERE username = ?", (username,))
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
    username = username.strip()
    password = password.strip()
    
    # 1. Admin login check
    if (username.lower() in ("admin", "superadmin", "مشرف") and password in (ADMIN_PASSWORD, ADMIN_KEY)) or password == ADMIN_PASSWORD:
        token = ADMIN_KEY
        return {
            "id": 0,
            "username": "admin",
            "role": "admin",
            "token": token,
            "is_admin": True
        }
        
    # 2. Database client user check
    u = db.one("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username.lower(),))
    if not u or not verify_password(password, u.get("password_hash", "")):
        raise ValueError("اسم المستخدم أو كلمة المرور غير صحيحة")
        
    uid = u["id"]
    role = u.get("role", "client")
    token = generate_token(uid, u["username"], role)
    return {
        "id": uid,
        "username": u["username"],
        "role": role,
        "token": token,
        "is_admin": (role == "admin")
    }


def check_user_limit(user: Dict[str, Any]) -> None:
    """Checks if the client has reached the 2-store limit. Raises ValueError if exceeded."""
    if not user or user.get("is_admin"):
        return  # Admin has no limit
        
    uid = user.get("id")
    uname = user.get("username", "")
    
    row = db.one(
        "SELECT count(*) as c FROM jobs WHERE user_id = ? OR client = ? OR client LIKE ?",
        (uid, uname, f"tg:{uname}%")
    )
    count = int(row.get("c", 0) or 0) if row else 0
    if count >= MAX_SITES_PER_CLIENT:
        raise ValueError(
            f"عفواً، لقد استنفدت الحد الأقصى المسموح به ({MAX_SITES_PER_CLIENT} مواقع) في باقتك الحالية! يرجى ترقية الحساب لإنشاء مواقع إضافية."
        )


def verify_site_ownership(jid: int, user: Optional[Dict[str, Any]]) -> bool:
    """Returns True if the user is the admin or the owner of the job."""
    if not user:
        return False
    if user.get("is_admin"):
        return True
        
    job = db.one("SELECT user_id, client FROM jobs WHERE id = ?", (jid,))
    if not job:
        return False
        
    uid = user.get("id")
    uname = user.get("username", "")
    if job.get("user_id") is not None and str(job.get("user_id")) == str(uid):
        return True
    if job.get("client") and str(job.get("client")).strip() == str(uname).strip():
        return True
    if uname and job.get("client") and job.get("client").startswith(f"tg:{uname}"):
        return True
    return False
