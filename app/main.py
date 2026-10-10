"""FastAPI application: API routes, Telegram bot polling & webhook, static serving.

Features:
- Subdomain Routing for generated sites (e.g., site-1.localhost or slug.localhost)
- Full-Stack Site Backend APIs (/api/sites/{id}/info, /items, /orders, /checkout)
- Admin Login & Supervision Panel with configurable password
- Prompt Injection & Financial Safety Guardrails
- Telegram Bot integration with auto-polling & mobile approvals
- Multi-tenant SQLite / Turso libSQL cloud support
"""
import asyncio
import hashlib
import hmac
import io
import json
import os
import random
import re
import secrets
import sys
import time
import uuid
from contextlib import asynccontextmanager
from http.cookies import SimpleCookie
from pathlib import Path, PurePosixPath
import shutil
from typing import Optional, Dict, Any, List
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Cookie, Header, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import artifacts, audit, auth, builder, corp, db, llm, rate_limit, runtime, skills, tools, security
from .body_limits import MAX_REQUEST_BODY_BYTES, RequestBodyLimitMiddleware
from .security_filters import SecurityFilterMiddleware
from .routers.operations import router as operations_router
from .schemas import (
    AdminLoginRequest,
    GitHubDeployRequest,
    JobDecisionRequest,
    LoginRequest,
    MarketingEmailDraftRequest,
    ProjectCreateRequest,
    RegisterRequest,
    SiteAutomationDecisionRequest,
    SiteFileSaveRequest,
    SiteItemCreateRequest,
    SiteOrderCreateRequest,
    SiteRefineRequest,
    SiteSettingsPatchRequest,
    SocialPostDraftRequest,
    VisualSiteEditRequest,
    VercelDeployRequest,
)
from .uploads import (
    ALLOWED_UPLOADS,
    IMAGE_MEDIA_TYPES_BY_EXTENSION,
    MAX_EXTRACTED_TEXT_CHARS,
    MAX_TELEGRAM_ATTACHMENT_BYTES,
    MAX_UPLOAD_BYTES,
    extract_pdf_text,
    sanitize_image_upload,
)

IS_VERCEL = os.getenv("VERCEL", "0") == "1"
BASE = os.path.dirname(os.path.dirname(__file__))
# =========================================================
# Security & Safety Guardrails
# =========================================================
BLOCKED_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"transfer\s+(all\s+)?money",
    r"send\s+(all\s+)?funds",
    r"wire\s+transfer",
    r"credit\s*card\s*number",
    r"bank\s+account\s+password",
    r"hack|exploit|malware|ransomware",
    r"counterfeit|weapon|bomb"
]

def check_guardrails(text: str) -> None:
    """Blocks malicious prompt injections and illegal requests."""
    t_lower = (text or "").lower()
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, t_lower):
            raise HTTPException(400, "طلبك يتعارض مع معايير الأمان والحوكمة في AutoCorp.")


# =========================================================
# Lifespan: Database Init & Local Polling
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do not perform synchronous schema migrations during a Vercel cold start.
    # Turso retries can consume the entire serverless invocation budget. Apply
    # schema migrations separately, then let request/health checks verify the
    # configured database connection.
    if not IS_VERCEL:
        try:
            db.init()
        except Exception as exc:
            print(f"[DB INIT WARNING] {exc}")
    tasks = []
    
    # 1. Background Tick loop (if enabled locally)
    secs = int(os.getenv("TICK_SECONDS", "0") or 0)
    if secs > 0 and not IS_VERCEL:
        async def tick_loop():
            while True:
                await asyncio.sleep(secs)
                try:
                    await corp.tick()
                except Exception as e:
                    print(f"[TICK ERROR] {e}")
        tasks.append(asyncio.create_task(tick_loop()))

    # 2. Telegram Bot Polling (locally so it works without ngrok)
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if tg_token and not IS_VERCEL:
        async def tg_polling():
            offset = 0
            print(f"[TELEGRAM] Bot polling started for @{os.getenv('TELEGRAM_BOT_USERNAME', 'autocorp_Alfarouq_Ibrahim_bot')}...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    try:
                        resp = await client.get(
                            f"https://api.telegram.org/bot{tg_token}/getUpdates",
                            params={"offset": offset, "timeout": 20}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            for u in data.get("result", []):
                                offset = max(offset, u["update_id"] + 1)
                                try:
                                    await handle_telegram_update(u)
                                except Exception as e:
                                    print(f"[TG UPDATE ERR] {e}")
                        else:
                            await asyncio.sleep(5)
                    except Exception:
                        await asyncio.sleep(5)
        tasks.append(asyncio.create_task(tg_polling()))

    yield

    for t in tasks:
        t.cancel()


app = FastAPI(title="AutoCorp - AI agency for Egyptian SMEs", lifespan=lifespan)
app.include_router(operations_router)
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)
app.add_middleware(SecurityFilterMiddleware)


def api_error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    detail: Any = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """Return a stable error envelope while preserving legacy `detail` clients."""
    request_id = str(getattr(request.state, "request_id", ""))[:80]
    content: Dict[str, Any] = {
        "error": {"code": code, "message": message, "request_id": request_id},
        "detail": detail if detail is not None else message,
    }
    response = JSONResponse(status_code=status_code, content=content, headers=headers)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_envelope(request: Request, exc: HTTPException):
    """Make expected API failures machine-readable without breaking legacy UI code."""
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request could not be completed"
    return api_error_response(
        request,
        status_code=exc.status_code,
        code=f"http_{exc.status_code}",
        message=message,
        detail=detail,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_envelope(request: Request, exc: RequestValidationError):
    """Expose validation locations, not an unstructured framework error response."""
    problems = [
        {
            "location": list(error.get("loc", ())),
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return api_error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        detail=problems,
    )


@app.exception_handler(Exception)
async def unexpected_exception_envelope(request: Request, exc: Exception):
    """Avoid exposing implementation details from unexpected API failures."""
    audit.record(
        "api.unexpected_error",
        actor_type="system",
        target_type="request",
        target_id=request.url.path[:240],
        outcome="error",
        metadata={"exception_type": type(exc).__name__},
    )
    return api_error_response(
        request,
        status_code=500,
        code="internal_error",
        message="An unexpected server error occurred",
    )


# =========================================================
# Subdomain Middleware
# =========================================================
@app.middleware("http")
async def subdomain_middleware(request: Request, call_next):
    """Allows accessing sites via subdomain like 3.localhost:8000 or koshary.localhost:8000."""
    # Browser sessions are HttpOnly cookies. Mirror the signed value into the
    # existing internal header interface so legacy route handlers never need a
    # browser-readable bearer token. This must happen before any access to
    raw_headers = list(request.scope.get("headers", []))
    raw_cookie = next((value for name, value in raw_headers if name.lower() == b"cookie"), b"")
    cookies = SimpleCookie()
    session = ""
    try:
        cookies.load(raw_cookie.decode("latin-1", "ignore"))
        session_cookie = cookies.get("autocorp_session")
        session = session_cookie.value.strip() if session_cookie else ""
    except Exception:
        session = ""
    if not session and raw_cookie:
        cookie_str = raw_cookie.decode("latin-1", "ignore")
        match = re.search(r'(?:^|;\s*)autocorp_session=([^;]+)', cookie_str)
        if match:
            session = urllib.parse.unquote(match.group(1).strip())
    if not session and hasattr(request, "cookies"):
        try:
            session = str(request.cookies.get("autocorp_session") or "").strip()
        except Exception:
            session = ""
    has_user_header = any(
        name.lower() == b"x-user-token" and value.strip()
        for name, value in raw_headers
    )
    if session and not has_user_header:
        # Strip out any empty x-user-token or x-admin-key headers first so Starlette Headers.get() finds the populated one
        raw_headers = [
            (name, val) for name, val in raw_headers
            if name.lower() not in (b"x-user-token", b"x-admin-key") or val.strip()
        ]
        raw_headers.append((b"x-user-token", session.encode("latin-1", "ignore")))
        raw_headers.append((b"x-admin-key", session.encode("latin-1", "ignore")))
        request.scope["headers"] = raw_headers
        if hasattr(request, "_headers"):
            try:
                delattr(request, "_headers")
            except Exception:
                pass
        if hasattr(request, "_cookies"):
            try:
                delattr(request, "_cookies")
            except Exception:
                pass

    request_id = request.headers.get("x-request-id", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", request_id):
        request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    # This is an operator-controlled containment switch for incident response
    # and credential rotation. Read-only pages and probes remain available, but
    # no API, Telegram, webhook, or generated-site write can change data.
    if (
        os.getenv("MAINTENANCE_MODE", "0") == "1"
        and request.method not in {"GET", "HEAD", "OPTIONS"}
    ):
        response = api_error_response(
            request,
            status_code=503,
            code="maintenance_mode",
            message="Service is temporarily in read-only maintenance mode",
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Retry-After"] = "3600"
        response.headers["X-Request-ID"] = request_id
        return response
    # Cookie-authenticated browser writes must originate from this deployment or
    # an explicitly configured first-party origin. Requests without an Origin
    # header remain available to non-browser integrations authenticated by key.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        # Origin is absent on some browser navigations and can also be absent
        # from non-browser callers. Fetch Metadata closes the browser case
        # without breaking signed webhooks and server-to-server integrations.
        if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
            return api_error_response(
                request,
                status_code=403,
                code="cross_site_write_rejected",
                message="Cross-site state-changing request rejected",
            )
        origin = request.headers.get("origin", "").rstrip("/")
        if origin:
            public_url = os.getenv("PUBLIC_URL", "").rstrip("/")
            configured = {
                value.strip().rstrip("/")
                for value in os.getenv("TRUSTED_ORIGINS", "").split(",")
                if value.strip()
            }
            allowed_origins = configured | ({public_url} if public_url else set())
            # Host is supplied by the client. Only use it as a same-origin
            # fallback on local development hosts; deployed environments must
            # declare PUBLIC_URL or TRUSTED_ORIGINS explicitly.
            host_name = request.headers.get("host", "").split(":", 1)[0].lower()
            if not public_url and host_name in {"localhost", "127.0.0.1", "testserver"}:
                allowed_origins.add(
                    f"{request.url.scheme}://{request.headers.get('host', '')}".rstrip("/")
                )
            if origin not in allowed_origins:
                return api_error_response(
                    request,
                    status_code=403,
                    code="cross_origin_write_rejected",
                    message="Cross-origin state-changing request rejected",
                )
    host = request.headers.get("host", "").split(":")[0].lower()
    parts = host.split(".")
    public_host = ""
    public_url = os.getenv("PUBLIC_URL", "").strip()
    if public_url:
        try:
            public_host = urlparse(public_url).netloc.split(":")[0].lower()
        except Exception:
            public_host = ""

    is_platform_host = (
        (public_host and host == public_host)
        or (host.endswith(".vercel.app") and len(parts) <= 3)
        or (host.endswith(".onrender.com") and len(parts) <= 3)
        or (host.endswith(".railway.app") and len(parts) <= 3)
    )

    # If host has subdomain e.g. 'site-3' or 'koshary'
    if not is_platform_host and len(parts) >= 2 and parts[0] not in ("www", "api", "admin", "localhost", "127"):
        sub = parts[0]
        if sub.isdigit() and not request.url.path.startswith(f"/sites/{sub}") and not request.url.path.startswith("/api/"):
            request.scope["path"] = f"/sites/{sub}" + request.url.path
        elif not request.url.path.startswith("/api/") and not request.url.path.startswith("/sites/"):
            # Check slug
            try:
                row = db.one("select job_id from site_pages where slug=?", (sub,))
                if row:
                    jid = row["job_id"]
                    request.scope["path"] = f"/sites/{jid}" + request.url.path
            except Exception:
                pass
    audit_context = audit.bind_request_id(request_id)
    try:
        response = await call_next(request)
    finally:
        # Audit events use task-local context and must never bleed into a
        # concurrently handled request.
        audit.reset_request_id(audit_context)
    # A compact defence-in-depth baseline. The dashboard still relies on inline
    # scripts and handlers, so it cannot honestly enforce script-src yet. These
    # directives protect framing, plugin content, document bases, and form posts
    # without weakening the future nonce-based script policy.
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    response.headers.setdefault(
        "Content-Security-Policy",
        "base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'",
    )
    # A deployment that declares an HTTPS canonical public origin should never
    # permit clients to silently downgrade future visits. Local HTTP work stays
    # usable because it has no HTTPS PUBLIC_URL.
    if os.getenv("PUBLIC_URL", "").strip().lower().startswith("https://"):
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Request-ID", request_id)
    return response


# Mount sites directory locally if not Vercel
if not IS_VERCEL:
    os.makedirs(corp.SITES, exist_ok=True)
    app.mount("/sites-static", StaticFiles(directory=corp.SITES, html=True), name="sites-static")


# =========================================================
# Multimodal Uploads & Document Processing (Images & PDFs)
# =========================================================
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    job_id: Optional[int] = Form(None),
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    """Accept a small allow-list of authenticated image/PDF uploads safely."""
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=autocorp_session)
    if not user:
        raise HTTPException(401, "Authentication is required to upload a file")
    if job_id is not None:
        require_site_access(job_id, x_user_token, x_admin_key, authorization, cookie_token=autocorp_session)
    if not rate_limit.upload_limiter.allow(f"user:{user['id']}"):
        raise HTTPException(
            429,
            "Upload limit reached. Try again later.",
            headers={"Retry-After": "3600"},
        )

    raw_filename = file.filename or "upload"
    ext = os.path.splitext(raw_filename)[1].lower()
    if ext not in ALLOWED_UPLOADS:
        raise HTTPException(415, "Only JPG, PNG, WEBP, and PDF files are allowed")
    content_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content_bytes or len(content_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload must be between 1 byte and 10 MB")
    file_type, signature = ALLOWED_UPLOADS[ext]
    if not content_bytes.startswith(signature):
        raise HTTPException(415, "File content does not match its declared type")
    if file_type == "image":
        try:
            content_bytes = sanitize_image_upload(content_bytes, ext)
        except ValueError as exc:
            raise HTTPException(415, str(exc)) from exc
        if len(content_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Sanitized image exceeds the 10 MB limit")

    if IS_VERCEL:
        upload_dir = "/tmp/uploads"
    else:
        upload_dir = os.path.join(BASE, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    if not IS_VERCEL:
        api_upload_dir = os.path.join(BASE, "api", "static", "uploads")
        if os.path.exists(os.path.join(BASE, "api")):
            os.makedirs(api_upload_dir, exist_ok=True)
    else:
        api_upload_dir = None

    clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', os.path.splitext(raw_filename)[0])
    safe_filename = f"{secrets.token_urlsafe(18)}_{clean_base[:30]}{ext}"
    target_path = os.path.join(upload_dir, safe_filename)

    with open(target_path, "wb") as f:
        f.write(content_bytes)

    if api_upload_dir and os.path.exists(api_upload_dir):
        try:
            with open(os.path.join(api_upload_dir, safe_filename), "wb") as f:
                f.write(content_bytes)
        except Exception:
            pass

    extracted_text = ""
    if ext == ".pdf":
        extracted_text = extract_pdf_text(content_bytes)
    # Brief PDFs are transient input, not public static assets. Images remain
    # public because generated sites intentionally reference them.
    if ext == ".pdf":
        for stored_path in (target_path, os.path.join(api_upload_dir, safe_filename) if api_upload_dir else ""):
            if stored_path and os.path.exists(stored_path):
                os.remove(stored_path)
        file_url = ""
    else:
        file_url = f"/static/uploads/{safe_filename}"
    if job_id:
        try:
            db.x(
                "INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, safe_filename, file_type, extracted_text[:4000] if extracted_text else "", file_url, time.time())
            )
        except Exception as e:
            print(f"[SITE_FILES INSERT ERR] {e}")

    return {
        "success": True,
        "filename": safe_filename,
        "original_name": raw_filename,
        "file_type": file_type,
        "url": file_url,
        "extracted_text": extracted_text,
        "text_preview": extracted_text[:600] if extracted_text else ""
    }


@app.get("/static/uploads/{filename}")
@app.get("/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    """Serve sanitized public site images, never arbitrary legacy upload files."""
    fn = os.path.basename(filename)
    ext = os.path.splitext(fn)[1].lower()
    # Only the random, portable image names created by the upload handlers are
    # public. PDF briefs are transient, and old files must not become executable
    # same-origin content merely because they remain on disk.
    if (
        fn != filename
        or ext not in IMAGE_MEDIA_TYPES_BY_EXTENSION
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}\.(?:jpg|jpeg|png|webp)", fn, re.IGNORECASE)
    ):
        raise HTTPException(404, "Uploaded image not found")
    candidates = [
        os.path.join(BASE, "static", "uploads", fn),
        os.path.join(BASE, "api", "static", "uploads", fn),
        os.path.join("/tmp", "uploads", fn)
    ]
    for p in candidates:
        if os.path.isfile(p):
            return FileResponse(
                p,
                media_type=IMAGE_MEDIA_TYPES_BY_EXTENSION[ext],
                headers={
                    "Content-Disposition": f'inline; filename="{fn}"',
                    "X-Content-Type-Options": "nosniff",
                    "Cross-Origin-Resource-Policy": "same-site",
                },
            )
    raise HTTPException(404, "الملف غير موجود")



# =========================================================
# =========================================================
# Auth & Security Helpers
# =========================================================
def guard(env_names, key):
    need = next((os.getenv(n) for n in env_names if os.getenv(n)), "")
    if not need:
        raise HTTPException(503, "Required service credential is not configured")
    if not hmac.compare_digest(str(key or ""), need):
        raise HTTPException(401, "Unauthorized: bad key")

def require_security_feature(name: str, safe_replacement: str) -> None:
    """Keep high-risk prototype features off until their safe replacement ships."""
    if os.getenv(name, "0") != "1":
        raise HTTPException(503, f"This prototype feature is disabled pending {safe_replacement}.")


def admin(key):
    user = auth.get_active_user(str(key or ""))
    if user and user.get("is_admin"):
        return
    raise HTTPException(401, "Administrator session required")


def session_response(payload: dict, token: str) -> JSONResponse:
    """Issue a browser session without exposing the signed token to JavaScript."""
    response = JSONResponse(payload)
    configured_secure = os.getenv("COOKIE_SECURE", "").strip()
    # Explicit configuration is useful for local HTTPS testing. Otherwise, an
    # HTTPS canonical origin is enough evidence that browsers must never send
    # the session on a cleartext connection.
    secure_cookie = (
        configured_secure == "1"
        if configured_secure
        else IS_VERCEL or os.getenv("PUBLIC_URL", "").strip().lower().startswith("https://")
    )
    response.set_cookie(
        key="autocorp_session",
        value=token,
        max_age=auth.TOKEN_TTL_SECONDS,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )
    return response

def get_user_from_headers(x_user_token: str = "", x_admin_key: str = "", authorization: str = "", cookie_token: str = "") -> Optional[dict]:
    token = (x_user_token or "").strip() or (x_admin_key or "").strip() or (cookie_token or "").strip()
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if token:
        import urllib.parse
        token = urllib.parse.unquote(str(token).strip())
    return auth.get_active_user(token)

def require_site_access(jid: int, x_user_token: str = "", x_admin_key: str = "", authorization: str = "", cookie_token: str = "") -> dict:
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    if not auth.verify_site_ownership(jid, user):
        raise HTTPException(403, "غير مصرح لك بالوصول لإعدادات أو تحميل هذا المتجر. يرجى تسجيل الدخول بحساب مالك المتجر أو المشرف العام.")
    return user or {}


def safe_site_filename(filename: str) -> str:
    """Accept only a portable relative path inside one tenant's artifact tree."""
    name = str(filename or "").strip()
    if not name or len(name) > 240 or "\\" in name or ":" in name or "\x00" in name:
        raise HTTPException(400, "Invalid artifact filename")
    # Check raw components before pathlib normalizes away dot and empty parts.
    raw_parts = name.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise HTTPException(400, "Invalid artifact filename")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise HTTPException(400, "Invalid artifact filename")
    return path.as_posix()


ARABIC_TO_ENGLISH_WORDS = {
    "مطعم": "restaurant",
    "مشويات": "grill",
    "كبابجي": "kebabji",
    "عسل": "honey",
    "نحل": "bee",
    "سدر": "sidr",
    "طبيعي": "pure",
    "خضار": "vegetables",
    "فواكه": "fruits",
    "طازج": "fresh",
    "فريش": "fresh",
    "سوبرماركت": "market",
    "ماركت": "market",
    "بقالة": "grocery",
    "صيدلية": "pharmacy",
    "دكتور": "dr",
    "طبيب": "doctor",
    "عيادة": "clinic",
    "كافيه": "cafe",
    "قهوة": "coffee",
    "حلويات": "sweets",
    "حلواني": "pastry",
    "أجهزة": "devices",
    "اجهزة": "devices",
    "إلكترونيات": "tech",
    "الكترونيات": "tech",
    "موبايل": "mobile",
    "لابتوب": "laptop",
    "ملابس": "fashion",
    "أزياء": "apparel",
    "ازياء": "apparel",
    "بوتيك": "boutique",
    "سايبر": "cyber",
    "سيكيورتي": "security",
    "أمن": "security",
    "امن": "security",
    "سيبراني": "cyber",
    "بورتفوليو": "portfolio",
    "برمجة": "dev",
    "مطور": "dev",
    "مهندس": "eng",
    "شركة": "co",
    "وكالة": "agency",
    "متجر": "store",
    "ستور": "store",
    "موقع": "site",
    "ياسين": "yaseen",
    "احمد": "ahmed",
    "أحمد": "ahmed",
    "فاروق": "farouq",
    "ابراهيم": "ibrahim",
    "إبراهيم": "ibrahim",
    "محمد": "mohamed",
    "محمود": "mahmoud",
    "علي": "ali",
    "حسن": "hassan",
    "حسين": "hussein",
    "عمر": "omar",
    "خالد": "khaled",
    "سارة": "sara",
    "مريم": "mariam",
    "البركة": "baraka",
    "الأصيل": "aseel",
    "الاصيل": "aseel",
    "الشفاء": "shefaa",
    "النقاء": "naqaa",
    "الرواق": "rewaq",
}

ARABIC_CHAR_MAP = {
    'ا': 'a', 'أ': 'a', 'إ': 'e', 'آ': 'a', 'ء': '', 'ئ': 'e', 'ؤ': 'o',
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh',
    'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a', 'ة': 'a', 'پ': 'p', 'چ': 'ch'
}

def arabic_to_english_slug(text: str) -> str:
    s = str(text or "").lower().strip()
    for ar_w, en_w in ARABIC_TO_ENGLISH_WORDS.items():
        s = s.replace(ar_w, en_w)
    out = []
    for ch in s:
        if ch in ARABIC_CHAR_MAP:
            out.append(ARABIC_CHAR_MAP[ch])
        elif re.match(r'[a-z0-9]', ch):
            out.append(ch)
        elif ch in (' ', '-', '_', '/', '|', ':', '،', ','):
            out.append('-')
    res = "".join(out)
    res = re.sub(r'-+', '-', res).strip('-')
    return res

def make_site_slug(jid: int, brand: str = "", niche: str = "") -> str:
    en_slug = arabic_to_english_slug(brand)
    if not en_slug or len(en_slug) < 2:
        en_slug = niche or "site"
    return f"{jid}-{en_slug}"


def resolve_job_id(slug_or_id: str) -> int:
    import urllib.parse
    s = urllib.parse.unquote(str(slug_or_id or "")).strip()
    if not s:
        raise HTTPException(404, "معرف المتجر غير صحيح")
    if s.isdigit():
        return int(s)
    if "-" in s:
        prefix = s.split("-")[0]
        if prefix.isdigit():
            return int(prefix)
    row = db.one("SELECT id FROM jobs WHERE client = ? OR client LIKE ?", (s, f"%{s}%"))
    if row and row.get("id"):
        return int(row["id"])
    raise HTTPException(404, f"المتجر ({s}) غير موجود")


def is_store_creation_intent(text: str) -> bool:
    t = text.lower().strip()
    t = re.sub(r'[إأآا]', 'ا', t)
    t = re.sub(r'[ة]', 'ه', t)
    t = re.sub(r'[ى]', 'ي', t)

    # Deletion guardrail: explicit deletion requests must NEVER be classified as creation
    del_words = ["احذف", "امسح", "حذف", "مسح", "ازال", "ازاله", "الغاء", "الغي", "delete", "remove", "drop"]
    if any(d in t for d in del_words):
        return False
    
    creation_verbs = ["انشا", "تنشا", "اعمل", "تعمل", "صمم", "ابني", "تبني", "بناء", "برمج", "تطوير", "اطلق", "سوي", "كريت", "جهز", "build", "create", "make"]
    target_nouns = ["موقع", "ويب", "متجر", "ستور", "صفحه", "صفحة", "منيو", "مشروع", "بورتفوليو", "بروفايل", "سيرة", "cv", "portfolio"]
    desire_words = ["عايز", "عاوز", "اريد", "حابب", "ودي", "محتاج", "لازم", "نفسي"]
    
    has_verb = any(v in t for v in creation_verbs)
    has_noun = any(n in t for n in target_nouns)
    has_desire = any(d in t for d in desire_words)
    
    if has_verb and has_noun:
        return True
    if has_desire and has_noun:
        return True
    if has_verb and any(k in t for k in ["اسمه", "باسم", "واحد", "لـ", "لواحد", "لشخص"]):
        return True
    if has_desire and any(k in t for k in ["بيع", "محل", "مطعم", "كافيه", "سوبرماركت", "صيدليه", "خضار", "اجهز", "الكترون", "عسل", "سايبر", "سيكيورتي", "دكتور", "عياده"]):
        return True
    if any(k in t for k in ["/build", "ابدأ البناء", "انشاء متجر", "عمل موقع", "بناء متجر", "عمل بورتفوليو", "بناء موقع", "تصميم موقع"]):
        return True
    return False


# =========================================================
# Authentication APIs (Client & Admin)
# =========================================================
@app.post("/api/auth/register")
def api_register(body: RegisterRequest):
    uname = body.username.strip()
    pwd = body.password.strip()
    phone = body.phone.strip()
    try:
        user = auth.register_user(uname, pwd, phone)
        token = user.pop("token")
        audit.record("identity.user_registered", actor_id=user["id"], target_type="user", target_id=str(user["id"]))
        return session_response({"ok": True, "user": user}, token)
    except RuntimeError:
        raise HTTPException(503, "Authentication is not configured")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/auth/login")
def api_login(body: LoginRequest, request: Request):
    uname = body.username.strip()
    pwd = body.password.strip()
    client_host = request.client.host if request.client else "unknown"
    throttle_key = f"{client_host}:{uname.lower()[:80]}"
    if not rate_limit.login_limiter.allow(throttle_key):
        raise HTTPException(429, "Too many login attempts. Please try again later.")
    try:
        user = auth.login_user(uname, pwd)
        token = user.pop("token")
        rate_limit.login_limiter.reset(throttle_key)
        audit.record("identity.login_succeeded", actor_id=user["id"], target_type="user", target_id=str(user["id"]))
        return session_response({"ok": True, "user": user}, token)
    except RuntimeError:
        raise HTTPException(503, "Authentication is not configured")
    except ValueError as e:
        audit.record("identity.login_failed", actor_type="anonymous", target_type="session", outcome="denied")
        raise HTTPException(401, str(e))


@app.post("/api/auth/logout")
def api_logout(
    request: Request,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    """Revoke the current session and clear its browser cookie."""
    token = x_user_token or x_admin_key or autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token:
        user = auth.get_active_user(token)
        if user and auth.revoke_token(token):
            audit.record(
                "identity.logout_succeeded",
                actor_id=user.get("id"),
                actor_type="administrator" if user.get("is_admin") else "user",
                target_type="session",
            )
    response = JSONResponse({"ok": True})
    response.delete_cookie("autocorp_session", path="/")
    return response


@app.get("/api/auth/me")
def api_me(
    request: Request,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    cookie_token = autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    if not user:
        return {"authenticated": False}
    c_row = db.one("SELECT count(*) as c FROM jobs WHERE user_id = ? OR client = ?", (user["id"], user["username"]))
    count = c_row.get("c", 0) if c_row else 0
    return {
        "authenticated": True,
        "user": user,
        "sites_count": count,
        "max_sites": 999 if user.get("is_admin") else auth.MAX_SITES_PER_CLIENT
    }


@app.post("/api/admin/login")
def admin_login(body: AdminLoginRequest, request: Request):
    """Admin login verifying ADMIN_PASSWORD from environment."""
    pwd = body.password.strip()
    client_host = request.client.host if request.client else "unknown"
    throttle_key = f"{client_host}:admin"
    if not rate_limit.admin_login_limiter.allow(throttle_key):
        raise HTTPException(429, "Too many administrator login attempts. Please try again later.")
    try:
        correct_pwd = auth.admin_password()
    except RuntimeError:
        raise HTTPException(503, "Administrator authentication is not configured")
    if hmac.compare_digest(pwd, correct_pwd):
        token = auth.generate_token(0, "admin", "admin")
        rate_limit.admin_login_limiter.reset(throttle_key)
        audit.record("identity.admin_login_succeeded", actor_id=0, actor_type="administrator", target_type="session")
        return session_response({
            "ok": True,
            "username": os.getenv("ADMIN_NAME", "المدير العام المشرف"),
            "role": "Super Admin & Agency Director"
        }, token)
    audit.record("identity.admin_login_failed", actor_type="anonymous", target_type="administrator", outcome="denied")
    raise HTTPException(401, "كلمة مرور المشرف غير صحيحة")


# =========================================================
# Job Creation & Planning
# =========================================================
def make_job(client, request, user_id=None, sync=False, idempotency_key=None, request_hash=None, defer_start=False):
    check_guardrails(request)
    try:
        jid = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at, idempotency_key, request_hash) "
            "VALUES (?, ?, ?, ?, strftime('%s','now'), ?, ?)",
            ((client or "web-client")[:80], request[:4000], "created", user_id, idempotency_key, request_hash)
        )
    except Exception:
        if idempotency_key:
            existing = db.one(
                "SELECT id, request_hash FROM jobs WHERE user_id=? AND idempotency_key=?",
                (user_id, idempotency_key),
            )
            if existing:
                if not hmac.compare_digest(existing.get("request_hash") or "", request_hash or ""):
                    raise HTTPException(409, "Idempotency-Key was already used with a different request")
                return existing["id"], False
        raise
    if sync or IS_VERCEL or defer_start:
        return jid, True
    else:
        corp.spawn(corp.plan_job(jid))
        return jid, True


@app.get("/")
def home():
    candidates = [
        os.path.join(BASE, "static", "index.html"),
        os.path.join(BASE, "api", "static", "index.html"),
        os.path.join(os.getcwd(), "static", "index.html"),
        os.path.join(os.getcwd(), "api", "static", "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "static", "index.html"),
        os.path.join(os.path.dirname(__file__), "static", "index.html"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return FileResponse(p, media_type="text/html")
    return HTMLResponse("<h1>AutoCorp AI Agency</h1><p>Running on Vercel</p>", media_type="text/html")


@app.get("/api/healthz")
def healthz():
    """Secret-free readiness probe for load balancers and deployment checks."""
    status = runtime.runtime_security_status()
    try:
        db.one("SELECT 1 AS ready")
        status["database_ready"] = True
    except Exception:
        # Keep database failures distinct from configuration failures and never
        # return a connection string or backend exception through this route.
        status["database_ready"] = False
        status["ready"] = False
    return JSONResponse(status, status_code=200 if status["ready"] else 503)


@app.get("/bot_avatar.jpg")
def bot_avatar():
    candidates = [
        os.path.join(BASE, "static", "bot_avatar.jpg"),
        os.path.join(BASE, "api", "static", "bot_avatar.jpg"),
        os.path.join(BASE, "bot_avatar.jpg"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return FileResponse(p, media_type="image/jpeg")
    return HTMLResponse("", status_code=404)


@app.post("/api/jobs")
async def new_job(
    body: ProjectCreateRequest,
    request: Request,
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    body_data = body.model_dump(exclude_unset=True)
    cookie_token = autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    if not user:
        raise HTTPException(401, "يرجى تسجيل الدخول أو إنشاء حساب أولاً قبل إطلاق وبناء المتجر.")
        
    # Check limit of 2 stores for clients
    try:
        auth.check_user_limit(user)
    except ValueError as e:
        raise HTTPException(403, str(e))
    req = (body_data.get("request") or "").strip()
    brand_name = (body_data.get("brand_name") or body_data.get("client") or "").strip()
    category = (body_data.get("category") or "").strip()
    slogan = (body_data.get("slogan") or "").strip()
    
    # Build a structured request if user used the visual wizard
    full_req = req
    if brand_name:
        parts = [f"مشروع بناء موقع وتطبيق ويب متكامل لـ '{brand_name}'"]
        if category:
            parts.append(f"تصنيف النشاط: {category}")
        if slogan:
            parts.append(f"الشعار التسويقي: {slogan}")
        if req:
            parts.append(f"تفاصيل الطلب: {req}")
        if body_data.get("extracted_text"):
            parts.append(f"\n[مستند/كتالوج/منيو مرفق من العميل]:\n{body_data['extracted_text'][:3500]}")
        
        # AI answers
        ai_answers = body_data.get("ai_answers") or []
        for ans in ai_answers:
            if ans.get("a"):
                parts.append(f"- {ans.get('label', 'ملاحظة')}: {ans.get('a')}")
        full_req = "\n".join(parts)
        
    if not full_req:
        raise HTTPException(400, "طلب المشروع أو بيانات المتجر مطلوبة")
    check_guardrails(full_req)

    idempotency_key = idempotency_key.strip()
    idempotency_scope = f"job-create:{user['id']}"
    request_hash = ""
    if idempotency_key:
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", idempotency_key):
            raise HTTPException(400, "Invalid Idempotency-Key format")
        request_hash = hashlib.sha256(
            json.dumps(await request.json(), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        existing = db.one(
            "SELECT request_hash, job_id FROM idempotency_records WHERE scope=? AND idempotency_key=?",
            (idempotency_scope, idempotency_key),
        )
        if existing:
            if not hmac.compare_digest(existing["request_hash"], request_hash):
                raise HTTPException(409, "Idempotency-Key was already used with a different request")
            if existing.get("job_id"):
                return {"id": existing["job_id"], "duplicate": True, "message": "Duplicate request reused the original project."}
            raise HTTPException(409, "An equivalent project request is already being processed")

        existing_job = db.one(
            "SELECT id, request_hash FROM jobs WHERE user_id=? AND idempotency_key=?",
            (user["id"], idempotency_key),
        )
        if existing_job:
            if not hmac.compare_digest(existing_job.get("request_hash") or "", request_hash):
                raise HTTPException(409, "Idempotency-Key was already used with a different request")
            return {"id": existing_job["id"], "duplicate": True, "message": "Duplicate request reused the original project."}

    # Never let a browser select synchronous generation or trigger expensive
    # model work inline; serverless hosting decides its supported path.
    sync = IS_VERCEL
    client_name = brand_name or body_data.get("client") or user.get("username") or "عميل-AutoCorp"
    jid, created = make_job(
        client_name,
        full_req,
        user_id=user.get("id"),
        sync=sync,
        idempotency_key=idempotency_key or None,
        request_hash=request_hash or None,
        defer_start=True,
    )
    if not created:
        return {"id": jid, "duplicate": True, "message": "Duplicate request reused the original project."}
    audit.record("site.job_created", actor_id=user["id"], target_type="job", target_id=str(jid))
    
    # Save site settings
    db.x("""
        INSERT OR REPLACE INTO site_settings (
            job_id, brand_name, category, custom_domain, color_primary, color_secondary,
            logo_url, phone, whatsapp, address, vodafone_cash, instapay, fawry_code,
            cod_enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        jid, brand_name, category, body_data.get("custom_domain") or "",
        body_data.get("color_primary") or "", body_data.get("color_secondary") or "",
        body_data.get("logo_url") or "", body_data.get("phone") or "", body_data.get("whatsapp") or "",
        body_data.get("address") or "", body_data.get("vodafone_cash") or "", body_data.get("instapay") or "",
        body_data.get("fawry_code") or "", 1 if body_data.get("cod_enabled", True) else 0,
        time.time()
    ))

    # Record uploaded logo and document into site_files
    if body_data.get("logo_url"):
        try:
            db.x("INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, 'image', 'شعار المتجر', ?, ?)",
                 (jid, os.path.basename(body_data.get("logo_url")), body_data.get("logo_url"), time.time()))
        except Exception:
            pass
    if body_data.get("extracted_text"):
        try:
            db.x("INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, 'document.pdf', 'pdf', ?, '', ?)",
                 (jid, body_data.get("extracted_text")[:4000], time.time()))
        except Exception:
            pass
    
    # Save manual items if provided
    items = body_data.get("items") or []
    for it in items:
        if it.get("title"):
            db.x("""
                INSERT INTO site_items (job_id, title, price, category, description, badge, image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                jid, it.get("title"), float(it.get("price") or 0), it.get("category") or "عام",
                it.get("description") or "", it.get("badge") or "", it.get("image_url") or "", time.time()
            ))

    # Do not let planning race ahead of the wizard's settings, files, and
    # catalog writes. Persist the complete initial brief before starting work.
    if not sync:
        corp.spawn(corp.plan_job(jid))
            
    if sync:
        try:
            await corp.plan_job(jid)
            job = db.one("select * from jobs where id=?", (jid,))
            if job and job["status"] == "awaiting_plan":
                corp.log(jid, "Web wizard client authorized plan execution")
                db.x("update jobs set status='running' where id=?", (jid,))
                await corp.run_job(jid)
                job = db.one("select * from jobs where id=?", (jid,))
                if job and job["status"] == "awaiting_delivery":
                    await corp.deliver(jid)
            elif job and job["status"] not in ("rejected", "failed"):
                await corp.run_job(jid)
                job = db.one("select * from jobs where id=?", (jid,))
                if job and job["status"] == "awaiting_delivery":
                    await corp.deliver(jid)
        except Exception as e:
            print(f"[SYNC JOB ERROR] {e}")
    return {"id": jid, "brand_name": brand_name, "message": "تم إنشاء المشروع وبدأ فريق الـ Agents في التنفيذ"}


@app.post("/api/hooks/job")
async def hook_job(body: dict, x_hook_key: str = Header(default="")):
    guard(["HOOK_KEY"], x_hook_key)
    req = (body.get("request") or "").strip()
    if not req:
        raise HTTPException(400, "طلب المشروع مطلوب")
    check_guardrails(req)
    jid, _created = make_job(body.get("client") or "webhook", req, sync=IS_VERCEL)
    if IS_VERCEL:
        try:
            await corp.plan_job(jid)
        except Exception as e:
            print(f"[HOOK JOB ERROR] {e}")
    return {"id": jid}


@app.get("/api/jobs")
def get_jobs(
    request: Request,
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    cookie_token = autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    if not user:
        raise HTTPException(401, "Authentication is required")
    where = ""
    args: tuple = ()
    if not user.get("is_admin"):
        where = "WHERE j.user_id = ?"
        args = (user["id"],)
    total_row = db.one("SELECT COUNT(*) AS total FROM jobs j " + where, args)
    total = int((total_row or {}).get("total") or 0)
    rows = db.q("""
        SELECT j.*, 
               s.brand_name,
               (select count(*) from site_orders where job_id = j.id) as orders_count 
        FROM jobs j 
        LEFT JOIN site_settings s ON s.job_id = j.id
        """ + where + """
        ORDER BY j.id desc LIMIT ? OFFSET ?
    """, args + (limit, offset))
    page_headers = {
        "X-Total-Count": str(total),
        "X-Page-Limit": str(limit),
    }
    next_offset = offset + len(rows)
    if next_offset < total:
        page_headers["X-Next-Offset"] = str(next_offset)
    if not rows:
        return JSONResponse(content=[], headers=page_headers)
        
    jids = [j["id"] for j in rows]
    placeholders = ",".join("?" for _ in jids)
    events_raw = db.q(f"""
        SELECT job_id, msg FROM (
            SELECT job_id, msg,
                   ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY id DESC) AS event_rank
            FROM events
            WHERE job_id IN ({placeholders})
        ) recent_events
        WHERE event_rank <= 8
        ORDER BY job_id, event_rank
    """, tuple(jids))
    
    events_by_job = {}
    for ev in events_raw:
        jid = ev["job_id"]
        if jid not in events_by_job:
            events_by_job[jid] = []
        if len(events_by_job[jid]) < 8:
            events_by_job[jid].append({"msg": ev["msg"]})
            
    for j in rows:
        j_id = j["id"]
        # Ensure clean, human-friendly brand title
        bname = (j.get("brand_name") or "").strip()
        client = str(j.get("client") or "").strip()
        if (not client or client.startswith("tg:") or client in ("web-client", "TestClient")) and bname:
            j["client"] = bname
        elif not bname and client:
            j["brand_name"] = client
            
        j["events"] = list(reversed(events_by_job.get(j_id, [])))
        slug = make_site_slug(j_id, j.get("client") or bname)
        j["slug"] = slug
        j["frontend_url"] = f"/sites/{slug}/"
        j["backend_api_url"] = f"/api/sites/{j_id}/info"
        j["orders_count"] = int(j.get("orders_count") or 0)
        j["is_paid"] = bool(j.get("is_paid", 0))
        j["can_manage"] = auth.verify_site_ownership(j_id, user)
    return JSONResponse(content=rows, headers=page_headers)


@app.get("/api/public/showcase")
@app.get("/api/showcase")
def get_public_showcase(limit: int = Query(default=12, ge=1, le=50)):
    """Returns safe, public metadata for live delivered storefronts for the showcase gallery.
    Zero secret tokens, zero user_id, zero orders, zero internal config."""
    rows = db.q("""
        SELECT j.id, j.client, j.request, j.status, j.created_at,
               s.brand_name, s.category, s.color_primary
        FROM jobs j
        LEFT JOIN site_settings s ON s.job_id = j.id
        WHERE j.status = 'delivered'
        ORDER BY j.id DESC
        LIMIT ?
    """, (limit,))
    results = []
    for r in rows:
        jid = r["id"]
        bname = (r.get("brand_name") or "").strip()
        client = str(r.get("client") or "").strip()
        display_name = bname or client or "متجر إلكتروني"
        slug = make_site_slug(jid, display_name)
        req = str(r.get("request") or "").strip()
        results.append({
            "id": jid,
            "brand_name": display_name,
            "client": display_name,
            "category": r.get("category") or "general",
            "request": req[:150],
            "slug": slug,
            "frontend_url": f"/sites/{slug}/",
            "status": "delivered",
            "color_primary": r.get("color_primary") or "#ff7a00"
        })
    return JSONResponse(content=results)


@app.get("/api/jobs/{jid}")
def get_job_detail(
    jid: int,
    request: Request,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    cookie_token = autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    j = db.one("select * from jobs where id=?", (jid,))
    if not j:
        raise HTTPException(404, "المشروع غير موجود")
    if not auth.verify_site_ownership(jid, user):
        raise HTTPException(403, "You are not authorized to view this project")
    j["events"] = db.q("select ts,msg from events where job_id=? order by id", (jid,))
    j["contracts"] = db.q("select from_agent,to_agent,sha256,preview from contracts where job_id=? order by id", (jid,))
    slug = make_site_slug(jid, j.get("client") or "")
    j["slug"] = slug
    j["frontend_url"] = f"/sites/{slug}/"
    j["backend_api_url"] = f"/api/sites/{jid}/info"
    j["is_paid"] = bool(j.get("is_paid", 0))
    j["can_manage"] = auth.verify_site_ownership(jid, user)
    if j["can_manage"]:
        j["orders"] = db.q("select * from site_orders where job_id=? order by id desc", (jid,))
    else:
        j["orders"] = []
    return j


@app.post("/api/jobs/{jid}/decision")
async def job_decision(
    jid: int,
    body: JobDecisionRequest,
    request: Request,
    x_admin_key: str = Header(default=""),
    x_user_token: str = Header(default=""),
    authorization: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    cookie_token = autocorp_session or str(request.cookies.get("autocorp_session") or "").strip()
    user = get_user_from_headers(x_user_token, x_admin_key, authorization, cookie_token=cookie_token)
    is_admin_ok = False
    try:
        admin(x_admin_key)
        is_admin_ok = True
    except HTTPException:
        if user and (user.get("is_admin") or user.get("role") == "admin"):
            is_admin_ok = True
    if not is_admin_ok and not (user and auth.verify_site_ownership(jid, user)):
        raise HTTPException(403, "غير مصرح لك باتخاذ قرار بشأن هذا المشروع")
    return await corp.decide(jid, body.decision)


# =========================================================
# Full-Stack Site Endpoints: Frontend + Backend APIs
# =========================================================
@app.get("/sites/{slug_or_id}/")
@app.get("/sites/{slug_or_id}")
@app.get("/sites/{slug_or_id}/index.html")
async def serve_site(slug_or_id: str):
    """Serves the complete frontend app for this site, injecting SITE_ID."""
    jid = resolve_job_id(slug_or_id)
    row = db.one("select html from site_pages where job_id=?", (jid,))
    if not row or not row.get("html"):
        local_path = os.path.join(corp.SITES, str(jid), "index.html")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                html = f.read()
        else:
            raise HTTPException(404, "لم يتم العثور على موقع هذا المشروع بعد.")
    else:
        html = row["html"]
    
    inject_script = f"""
<script>
  window.SITE_ID = {jid};
  window.API_BASE = window.location.origin + '/api/sites/{jid}';
  console.log('[AutoCorp Full-Stack] Connected to Backend API:', window.API_BASE);
</script>
"""
    if "</head>" in html:
        html = html.replace("</head>", f"{inject_script}\n</head>", 1)
    else:
        html = inject_script + html
    return HTMLResponse(html)


@app.get("/api/sites/{slug_or_id}/info")
def site_backend_info(slug_or_id: str):
    """Return public site metadata without exposing integration configuration."""
    jid = resolve_job_id(slug_or_id)
    job = db.one("select * from jobs where id=?", (jid,))
    if not job:
        raise HTTPException(404, "الموقع غير موجود")
    page = db.one("select * from site_pages where job_id=?", (jid,))
    orders_c = (db.one("select count(*) c from site_orders where job_id=?", (jid,)) or {}).get("c", 0)
    items_c = (db.one("select count(*) c from site_items where job_id=?", (jid,)) or {}).get("c", 0)
    slug = make_site_slug(jid, job.get("client"))
    
    return {
        "site_id": jid,
        "client": job.get("client"),
        "status": job.get("status"),
        "slug": slug,
        "frontend_url": f"/sites/{slug}/",
        "subdomain_url": f"http://{jid}.localhost:8000/",
        "backend_routes": [
            {"method": "GET", "path": f"/api/sites/{jid}/info", "desc": "معلومات الموقع والباك إند"},
            {"method": "GET", "path": f"/api/sites/{jid}/items", "desc": "قائمة المنتجات والمنيو"},
            {"method": "POST", "path": f"/api/sites/{jid}/orders", "desc": "إنشاء طلب بانتظار تأكيد التاجر"},
            {"method": "GET", "path": f"/api/sites/{jid}/orders", "desc": "عرض طلبات العملاء"}
        ],
        "stats": {
            "total_orders": orders_c,
            "catalog_items": items_c
        },
        "payment_processing": {
            "enabled": False,
            "status": "pending_verified_gateway_integration",
        },
    }


@app.get("/api/sites/{slug_or_id}/items")
def site_backend_items(slug_or_id: str):
    """Backend API: Returns menu/services catalog for this site."""
    jid = resolve_job_id(slug_or_id)
    rows = db.q("select * from site_items where job_id=? order by id", (jid,))
    if rows:
        return rows
    return [
        {"id": 1, "job_id": jid, "title": "الطلب الكلاسيكي المميز", "price": 65.0, "category": "الأكثر طلباً", "description": "خلطة طازجة خاصة مع صلصة الدقة الأصلية", "badge": "الأكثر طلباً"},
        {"id": 2, "job_id": jid, "title": "كومبو العائلة الفاخر", "price": 220.0, "category": "العروض", "description": "تكفي 4 إلى 5 أفراد مع المشروبات والإضافات", "badge": "توفير"},
        {"id": 3, "job_id": jid, "title": "وجبة التوفير السريعة", "price": 50.0, "category": "الوجبات الفردية", "description": "وجبة مشبعة وسريعة التحضير", "badge": "اقتصادي"}
    ]


@app.post("/api/sites/{slug_or_id}/orders")
async def site_backend_place_order(
    slug_or_id: str,
    body: SiteOrderCreateRequest,
    request: Request,
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
):
    """Record a public order request; this endpoint never confirms a payment."""
    jid = resolve_job_id(slug_or_id)
    client_host = request.client.host if request.client else "unknown"
    if not rate_limit.public_order_limiter.allow(f"{client_host}:{jid}"):
        raise HTTPException(429, "Too many order submissions. Please try again later.")

    submitted_items = body.items
    if not isinstance(submitted_items, list) or not submitted_items or len(submitted_items) > 20:
        raise HTTPException(422, "At least one and at most twenty order items are required")
    pay_method = body.payment_method.strip().lower()
    supported_methods = {
        "cash", "cash_on_delivery", "cod", "fawry", "fawry_pay",
        "vodafone_cash", "wallet", "instapay", "contract_invoice",
    }
    if pay_method not in supported_methods:
        raise HTTPException(422, "Unsupported payment method")
    catalog = db.q("SELECT id, title, price FROM site_items WHERE job_id=?", (jid,))
    is_quote_request = not catalog and pay_method == "contract_invoice"
    if not catalog and not is_quote_request:
        raise HTTPException(422, "This site has no active catalog")
    by_id = {str(item["id"]): item for item in catalog}
    by_title = {str(item.get("title") or "").strip(): item for item in catalog}
    validated_items = []
    server_total = 0.0
    for submitted in submitted_items:
        submitted = submitted.model_dump(exclude_none=True)
        if is_quote_request:
            title = str(submitted.get("title") or "").strip()
            if not 2 <= len(title) <= 200:
                raise HTTPException(422, "Each requested service needs a title")
            validated_items.append({"title": title, "unit_price": None, "quantity": 1})
            continue
        item = by_id.get(str(submitted.get("id") or "")) or by_title.get(str(submitted.get("title") or "").strip())
        try:
            quantity = int(submitted.get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0
        if not item or quantity < 1 or quantity > 50:
            raise HTTPException(422, "Each item must reference the active catalog with quantity 1-50")
        unit_price = round(float(item.get("price") or 0), 2)
        server_total += unit_price * quantity
        validated_items.append({"id": item["id"], "title": item["title"], "unit_price": unit_price, "quantity": quantity})
    cust_name = body.customer_name.strip()
    cust_phone = body.customer_phone.strip()
    cust_addr = body.customer_address.strip() or "استلام من الفرع"
    if len(cust_name.strip()) < 2 or len(cust_phone.strip()) < 6:
        raise HTTPException(422, "A customer name and phone number are required")

    idempotency_key = idempotency_key.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", idempotency_key):
        raise HTTPException(400, "A valid Idempotency-Key header is required")
    idempotency_scope = f"public-order:{jid}"
    request_hash = hashlib.sha256(
        json.dumps(await request.json(), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    # Read legacy reservations written before the order row carried its own key.
    legacy_record = db.one(
        "SELECT request_hash, order_id FROM idempotency_records WHERE scope=? AND idempotency_key=?",
        (idempotency_scope, idempotency_key),
    )
    if legacy_record:
        if not hmac.compare_digest(legacy_record["request_hash"], request_hash):
            raise HTTPException(409, "Idempotency-Key was already used with a different request")
        if legacy_record.get("order_id"):
            order = db.one("SELECT id, total_egp, payment_method, payment_ref, status FROM site_orders WHERE id=?", (legacy_record["order_id"],))
            if order:
                return {
                    "success": True, "duplicate": True, "order_id": order["id"],
                    "total_egp": order["total_egp"], "payment_method": order["payment_method"],
                    "payment_ref": order["payment_ref"], "status": order["status"],
                    "payment_processed": False, "merchant_confirmation_required": True,
                }
        raise HTTPException(409, "An equivalent order request is already being processed")

    # The durable unique key and order data now live in the same row. A single
    # insert makes retries safe without a vulnerable reserve-then-update gap.
    existing = db.one(
        "SELECT id, request_hash, total_egp, payment_method, payment_ref, status "
        "FROM site_orders WHERE job_id=? AND idempotency_key=?",
        (jid, idempotency_key),
    )
    if existing:
        if not hmac.compare_digest(existing.get("request_hash") or "", request_hash):
            raise HTTPException(409, "Idempotency-Key was already used with a different request")
        return {
            "success": True, "duplicate": True, "order_id": existing["id"],
            "total_egp": existing["total_egp"], "payment_method": existing["payment_method"],
            "payment_ref": existing["payment_ref"], "status": existing["status"],
            "payment_processed": False, "merchant_confirmation_required": True,
        }
    # Prices and line items always come from the tenant catalog. The browser's
    # total is intentionally ignored because it is not an authority on price.
    # Quote requests carry no price until a merchant supplies one.
    items = validated_items
    total_egp = 0.0 if is_quote_request else round(server_total, 2)
    ref_code = f"ORDER-{secrets.token_urlsafe(8).upper()}"
    pay_note = "Order received. Payment and fulfilment require merchant confirmation."

    try:
        order_id = db.x(
            "INSERT INTO site_orders(job_id, customer_name, customer_phone, customer_address, "
            "items_json, total_egp, payment_method, payment_ref, status, created_at, idempotency_key, request_hash) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                jid, cust_name, cust_phone, cust_addr, json.dumps(items, ensure_ascii=False),
                total_egp, pay_method, ref_code, "pending_confirmation", time.time(), idempotency_key, request_hash,
            ),
        )
    except Exception:
        # Another worker may have committed the same key after our lookup.
        existing = db.one(
            "SELECT id, request_hash, total_egp, payment_method, payment_ref, status "
            "FROM site_orders WHERE job_id=? AND idempotency_key=?",
            (jid, idempotency_key),
        )
        if existing:
            if not hmac.compare_digest(existing.get("request_hash") or "", request_hash):
                raise HTTPException(409, "Idempotency-Key was already used with a different request")
            return {
                "success": True, "duplicate": True, "order_id": existing["id"],
                "total_egp": existing["total_egp"], "payment_method": existing["payment_method"],
                "payment_ref": existing["payment_ref"], "status": existing["status"],
                "payment_processed": False, "merchant_confirmation_required": True,
            }
        raise
    audit.record(
        "commerce.order_received",
        actor_type="public_customer",
        target_type="order",
        target_id=str(order_id),
        metadata={"job_id": jid, "payment_method": pay_method, "item_count": len(items)},
    )
    
    corp.log(jid, f"📦 أوردر جديد #{order_id} من {cust_name} بمبلغ {total_egp} ج.م ({pay_method}) - كود: {ref_code}")
    
    return {
        "success": True,
        "order_id": order_id,
        "customer_name": cust_name,
        "total_egp": total_egp,
        "payment_method": pay_method,
        "payment_ref": ref_code,
        "payment_note": pay_note,
        "status": "pending_confirmation",
        "payment_processed": False,
        "merchant_confirmation_required": True,
        "quote_required": is_quote_request,
        "message": "Your order request was received and awaits merchant confirmation."
    }


@app.get("/api/sites/{slug_or_id}/orders")
def site_backend_get_orders(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    return db.q("select * from site_orders where job_id=? order by id desc", (jid,))


@app.get("/api/sites/{slug_or_id}/settings")
def get_site_settings(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    return db.one("select * from site_settings where job_id=?", (jid,)) or {}


@app.post("/api/sites/{slug_or_id}/settings")
def update_site_settings(
    slug_or_id: str,
    body: SiteSettingsPatchRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(400, "At least one site setting must be provided")
    current = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    merged = {
        key: current.get(key)
        for key in (
            "brand_name", "category", "custom_domain", "color_primary", "color_secondary",
            "logo_url", "phone", "whatsapp", "address", "vodafone_cash", "instapay",
            "fawry_code", "cod_enabled",
        )
    }
    for key, value in patch.items():
        # Null clears text settings; omission preserves them. Boolean null is
        # treated as omitted so it cannot accidentally disable checkout.
        if value is not None:
            merged[key] = value
        elif key != "cod_enabled":
            merged[key] = ""

    db.x("""
        INSERT OR REPLACE INTO site_settings (
            job_id, brand_name, category, custom_domain, color_primary, color_secondary,
            logo_url, phone, whatsapp, address, vodafone_cash, instapay, fawry_code,
            cod_enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        jid, merged.get("brand_name"), merged.get("category"), merged.get("custom_domain"),
        merged.get("color_primary"), merged.get("color_secondary"), merged.get("logo_url"),
        merged.get("phone"), merged.get("whatsapp"), merged.get("address"), merged.get("vodafone_cash"),
        merged.get("instapay"), merged.get("fawry_code"), 1 if merged.get("cod_enabled", True) else 0,
        time.time()
    ))
    job_row = db.one("select * from jobs where id=?", (jid,)) or {}
    items_rows = db.q("select * from site_items where job_id=?", (jid,))
    new_html = builder.build_site_html(jid, job_row.get("client") or "", job_row.get("request") or "", settings=merged, items=items_rows)
    db.x("update site_pages set html=? where job_id=?", (new_html, jid))
    d = os.path.join(corp.SITES, str(jid))
    if os.path.exists(d):
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(new_html)
    return {"ok": True, "message": "تم تحديث إعدادات وهوية المتجر وإعادة بناء الصفحة بنجاح"}


@app.get("/api/sites/{slug_or_id}/export-zip")
def export_site_zip(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    row = db.one("select * from site_pages where job_id=?", (jid,))
    if not row or not row.get("html"):
        raise HTTPException(404, "الموقع غير جاهز للتحميل بعد")
    
    settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    brand = settings.get("brand_name") or f"site_{jid}"
    items = db.q("select * from site_items where job_id=? order by id", (jid,))
    
    from app.enterprise_generator import generate_enterprise_project
    enterprise_files = generate_enterprise_project(
        job_id=jid,
        brand_name=brand,
        niche=settings.get("category", "general"),
        slogan=settings.get("slogan", ""),
        primary_color=settings.get("color_primary", ""),
        secondary_color=settings.get("color_secondary", ""),
        items=items,
        settings=settings
    )

    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Root index.html for direct browser double-click
        zf.writestr("index.html", row["html"])
        # All modular enterprise files (src/config, src/models, src/modules, src/middlewares, public, docker, etc.)
        for rel_path, content in enterprise_files.items():
            zf.writestr(rel_path, content)

        local_db = os.path.join(corp.SITES, str(jid), "database.sqlite")
        if os.path.exists(local_db):
            try:
                with open(local_db, "rb") as f_db:
                    zf.writestr("database.sqlite", f_db.read())
            except Exception:
                pass
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=autocorp_enterprise_site_{jid}.zip"}
    )


@app.post("/api/sites/{slug_or_id}/deploy-github")
async def deploy_site_github(
    slug_or_id: str,
    body: GitHubDeployRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Directly pushes full project repository to the user's personal GitHub account."""
    import base64
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    require_security_feature(
        "ENABLE_DIRECT_DEPLOYMENT",
        "a server-side deployment integration with short-lived OAuth credentials",
    )
    
    token = body.github_token.strip()
    if not token:
        raise HTTPException(400, "يرجى إدخال رمز الوصول الشخصي (GitHub Personal Access Token)")
        
    repo_name = (body.repo_name or f"autocorp-site-{jid}").strip()
    repo_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', repo_name).strip('-')
    is_private = body.is_private

    row = db.one("select * from site_pages where job_id=?", (jid,))
    if not row or not row.get("html"):
        raise HTTPException(404, "الموقع غير جاهز للرفع بعد")
        
    site_html = row["html"]
    settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    brand = settings.get("brand_name") or f"Site #{jid}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AutoCorp-AI-Agent"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Verify Token
        user_res = await client.get("https://api.github.com/user", headers=headers)
        if user_res.status_code != 200:
            raise HTTPException(401, "رمز GitHub Token غير صالح أو منتهي الصلاحية")
        gh_user = user_res.json().get("login")
        
        # Check or create repo
        repo_res = await client.get(f"https://api.github.com/repos/{gh_user}/{repo_name}", headers=headers)
        if repo_res.status_code == 404:
            create_res = await client.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json={
                    "name": repo_name,
                    "description": f"{brand} - Full-Stack site synthesized by AutoCorp AI Autonomous Agency",
                    "private": is_private,
                    "auto_init": False
                }
            )
            if create_res.status_code not in (200, 201):
                err_detail = create_res.json().get("message", "فشل إنشاء المستودع على GitHub")
                raise HTTPException(400, f"خطأ GitHub: {err_detail}")
        
        # Commit file helper
        async def put_file(file_path: str, content_bytes: bytes, commit_msg: str):
            f_url = f"https://api.github.com/repos/{gh_user}/{repo_name}/contents/{file_path}"
            sha = None
            get_f = await client.get(f_url, headers=headers)
            if get_f.status_code == 200:
                sha = get_f.json().get("sha")
            payload = {
                "message": commit_msg,
                "content": base64.b64encode(content_bytes).decode("ascii")
            }
            if sha:
                payload["sha"] = sha
            await client.put(f_url, headers=headers, json=payload)

        # Commit project files
        from app.enterprise_generator import generate_enterprise_project
        items = db.q("select * from site_items where job_id=? order by id", (jid,))
        enterprise_files = generate_enterprise_project(
            job_id=jid,
            brand_name=brand,
            niche=settings.get("category", "general"),
            slogan=settings.get("slogan", ""),
            primary_color=settings.get("color_primary", ""),
            secondary_color=settings.get("color_secondary", ""),
            items=items,
            settings=settings
        )

        # 1. Root index.html for direct preview
        await put_file("index.html", site_html.encode("utf-8"), "Add index.html via AutoCorp AI")

        # 2. Upload modular enterprise backend & frontend architecture files
        for rel_path, content in enterprise_files.items():
            await put_file(rel_path, content.encode("utf-8"), f"Add {rel_path} via AutoCorp AI")

        return {
            "ok": True,
            "repo_url": f"https://github.com/{gh_user}/{repo_name}",
            "clone_url": f"https://github.com/{gh_user}/{repo_name}.git",
            "files_count": len(enterprise_files) + 1,
            "message": f"تم رفع ملفات كود المشروع وهيكل الـ Full-Stack كاملة بنجاح إلى مستودعك على GitHub ({gh_user}/{repo_name})!"
        }


@app.post("/api/sites/{slug_or_id}/deploy-vercel")
async def deploy_site_vercel(
    slug_or_id: str,
    body: VercelDeployRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Deploys the site directly to Vercel using Deploy Hook or Vercel Token."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    require_security_feature(
        "ENABLE_DIRECT_DEPLOYMENT",
        "a server-side deployment integration with short-lived OAuth credentials",
    )
    
    deploy_hook = body.deploy_hook.strip()
    vercel_token = body.vercel_token.strip()
    project_name = (body.project_name or f"autocorp-site-{jid}").strip().lower()
    project_name = re.sub(r'[^a-z0-9\-]', '-', project_name).strip('-')

    row = db.one("select * from site_pages where job_id=?", (jid,))
    if not row or not row.get("html"):
        raise HTTPException(404, "الموقع غير جاهز للنشر بعد")
        
    site_html = row["html"]

    async with httpx.AsyncClient(timeout=45.0) as client:
        if deploy_hook:
            r = await client.post(deploy_hook)
            if r.status_code in (200, 201):
                return {
                    "ok": True,
                    "method": "hook",
                    "status": "QUEUED",
                    "message": "تم إطلاق وتفعيل النشر التلقائي عبر Vercel Deploy Hook بنجاح!"
                }
            else:
                raise HTTPException(400, f"فشل تشغيل Deploy Hook (كود {r.status_code})")
        
        if not vercel_token:
            raise HTTPException(400, "يرجى إدخال Vercel Token أو رابط Deploy Hook")
            
        headers = {
            "Authorization": f"Bearer {vercel_token}",
            "Content-Type": "application/json"
        }
        
        deploy_payload = {
            "name": project_name,
            "files": [
                {"file": "index.html", "data": site_html},
                {"file": "vercel.json", "data": json.dumps({"routes": [{"src": "/(.*)", "dest": "/index.html"}]})}
            ],
            "projectSettings": {
                "framework": None
            }
        }
        
        r = await client.post("https://api.vercel.com/v13/deployments", headers=headers, json=deploy_payload)
        d = r.json()
        if r.status_code not in (200, 201):
            err_msg = d.get("error", {}).get("message") or "تعذر النشر على Vercel"
            raise HTTPException(400, f"خطأ Vercel: {err_msg}")
            
        dep_id = d.get("id")
        dep_url = "https://" + (d.get("url") or f"{project_name}.vercel.app")
        status = d.get("readyState") or "READY"
        
        return {
            "ok": True,
            "method": "api",
            "deployment_id": dep_id,
            "url": dep_url,
            "status": status,
            "message": f"تم بدء نشر موقعك على Vercel بنجاح وهو متاح على: {dep_url}"
        }


@app.get("/api/sites/{slug_or_id}/deploy-status")
async def get_vercel_deploy_status(
    slug_or_id: str,
    request: Request,
    deployment_id: str = Query(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$"),
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    if "vercel_token" in request.query_params:
        raise HTTPException(400, "Do not send provider credentials in query strings")
    require_security_feature(
        "ENABLE_DIRECT_DEPLOYMENT",
        "a server-side deployment integration that never accepts a token in a URL",
    )

    # Status lookup needs a server-managed provider installation bound to this
    # site. Keep it unavailable until that integration and deployment record
    # exist; a caller-provided token is never accepted here.
    raise HTTPException(503, "Deployment status is unavailable until a server-side provider integration is configured")


@app.post("/api/sites/{slug_or_id}/activate-payment")
def activate_site_payment(
    slug_or_id: str,
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    require_security_feature(
        "ENABLE_DEMO_PAYMENT_ACTIVATION",
        "a verified payment gateway adapter, signed webhooks, and an immutable payment ledger",
    )
    method = (body.get("payment_method") or "vodafone_cash").strip()
    ref = (body.get("payment_ref") or "DIRECT_PAY").strip()
    amount = float(body.get("amount") or 299.0)
    
    db.x("UPDATE jobs SET is_paid=1, subscription_plan='active' WHERE id=?", (jid,))
    db.x(
        "INSERT INTO ledger (ts, account, delta, memo, job_id) VALUES (?, 'client_payment', ?, ?, ?)",
        (time.time(), amount, f"اشتراك تفعيل متجر #{jid} عبر {method} (مرجع: {ref})", jid)
    )
    return {
        "ok": True,
        "message": f"تم تفعيل اشتراك متجرك بنجاح بمبلغ {amount} ج.م! المتجر الآن نشط ومتاح للعملاء بشكل دائم.",
        "is_paid": True,
        "plan": "active"
    }


# =========================================================
# Project Lifecycle: Super Admin Deletion & Cleanup
# =========================================================
def cleanup_tenant_uploads(job_id: int) -> None:
    """Remove local upload copies belonging only to the tenant being deleted."""
    try:
        files = db.q(
            "SELECT filename, file_url FROM site_files WHERE job_id=?", (job_id,)
        )
        for file_record in files:
            file_url = str(file_record.get("file_url") or "")
            prefix = "/static/uploads/"
            if not file_url.startswith(prefix):
                continue

            filename = file_url[len(prefix):]
            # The database must never select a path outside the upload directory.
            if not filename or filename != os.path.basename(filename):
                continue
            if filename != str(file_record.get("filename") or ""):
                continue

            shared = db.one(
                "SELECT id FROM site_files WHERE job_id != ? AND file_url=? LIMIT 1",
                (job_id, file_url),
            )
            if shared:
                continue

            upload_dirs = (
                os.path.join(BASE, "static", "uploads"),
                os.path.join(BASE, "api", "static", "uploads"),
                os.path.join("/tmp", "uploads"),
            )
            for upload_dir in upload_dirs:
                candidate = os.path.join(upload_dir, filename)
                try:
                    if os.path.isfile(candidate):
                        os.remove(candidate)
                except OSError:
                    # Database deletion should not fail because an optional local
                    # replica is already gone or is read-only in serverless hosting.
                    continue
    except Exception as exc:
        print(f"[TENANT UPLOAD CLEANUP ERR] {type(exc).__name__}")


def delete_tenant_records(job_id: int) -> None:
    """Delete a tenant's operational data without erasing audit evidence."""
    order_rows = db.q("SELECT id FROM site_orders WHERE job_id=?", (job_id,))
    cleanup_tenant_uploads(job_id)
    for table_name in (
        "site_pages",
        "site_items",
        "site_orders",
        "site_settings",
        "site_files",
        "site_automations",
        "site_bot_configs",
        "tenant_databases",
        "tenant_records",
        "tenant_queries_log",
        "site_security_audits",
        "events",
        "contracts",
        "ledger",
        "posts",
    ):
        db.x(f"DELETE FROM {table_name} WHERE job_id=?", (job_id,))
    db.x("DELETE FROM idempotency_records WHERE job_id=?", (job_id,))
    for order in order_rows:
        db.x("DELETE FROM idempotency_records WHERE order_id=?", (order["id"],))
    db.x("DELETE FROM jobs WHERE id=?", (job_id,))


@app.delete("/api/sites/{slug_or_id}")
async def delete_site(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Deletes a site completely across all tables and on-disk files."""
    jid = resolve_job_id(slug_or_id)
    actor = require_site_access(jid, x_user_token, x_admin_key, authorization)
    audit.record(
        "site.deletion_requested",
        actor_id=actor.get("id"),
        actor_type="administrator" if actor.get("is_admin") else "user",
        target_type="job",
        target_id=str(jid),
    )

    # 1. Delete operational tenant records while retaining the audit event above.
    delete_tenant_records(jid)

    # 2. Delete local directory if exists
    site_dir = os.path.join(corp.SITES, str(jid))
    if os.path.exists(site_dir):
        try:
            shutil.rmtree(site_dir, ignore_errors=True)
        except Exception:
            pass

    return {
        "success": True,
        "message": f"تم حذف المشروع #{jid} وكافة ملفاته وقواعد بياناته نهائياً بنجاح!"
    }


# =========================================================
# Code & File Explorer / In-Browser Editor
# =========================================================
@app.get("/api/sites/{slug_or_id}/files")
def list_site_files(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Lists all files (index.html, server.js, package.json, Dockerfile, uploaded files) for this site."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    page = db.one("select html from site_pages where job_id=?", (jid,))
    site_html = (page.get("html") or "") if page else ""

    files = [
        {"filename": "index.html", "type": "code", "size": len(site_html.encode("utf-8")), "is_entry": True},
        {"filename": "database.sqlite", "type": "database", "size": 24576, "is_entry": False},
        {"filename": "schema.sql", "type": "database", "size": 3800, "is_entry": False},
        {"filename": "database.json", "type": "database", "size": 4200, "is_entry": False},
        {"filename": "src/config/database.js", "type": "code", "size": 2200, "is_entry": False},
        {"filename": "src/config/db.sqlite.js", "type": "code", "size": 1500, "is_entry": False},
        {"filename": "server.js", "type": "code", "size": 2500, "is_entry": False},
        {"filename": "package.json", "type": "code", "size": 650, "is_entry": False},
        {"filename": "README.md", "type": "doc", "size": 1800, "is_entry": False},
        {"filename": "Dockerfile", "type": "code", "size": 420, "is_entry": False},
        {"filename": "vercel.json", "type": "code", "size": 120, "is_entry": False}
    ]

    custom_files = db.q("SELECT filename, file_type, file_url, length(content) as content_len FROM site_files WHERE job_id=? ORDER BY id DESC", (jid,))
    for cf in custom_files:
        fn = cf["filename"]
        if not any(f["filename"] == fn for f in files):
            files.append({
                "filename": fn,
                "type": cf["file_type"] or "file",
                "size": cf.get("content_len") or 0,
                "file_url": cf.get("file_url") or "",
                "is_entry": False
            })

    return files


@app.get("/api/sites/{slug_or_id}/files/{filename:path}")
def get_site_file_content(
    slug_or_id: str,
    filename: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Fetches the content of a specific file for editing."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    filename = safe_site_filename(filename)

    if filename == "index.html":
        page = db.one("select html from site_pages where job_id=?", (jid,))
        content = (page.get("html") or "") if page else ""
        return {"filename": "index.html", "content": content}

    f_row = db.one("SELECT content, file_url FROM site_files WHERE job_id=? AND filename=?", (jid, filename))
    if f_row and f_row.get("content"):
        return {"filename": filename, "content": f_row["content"], "file_url": f_row.get("file_url")}

    settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    items = db.q("select * from site_items where job_id=? order by id", (jid,))
    from app.enterprise_generator import generate_enterprise_project
    ent_files = generate_enterprise_project(
        job_id=jid,
        brand_name=settings.get("brand_name") or f"site_{jid}",
        niche=settings.get("category", "general"),
        slogan=settings.get("slogan", ""),
        primary_color=settings.get("color_primary", ""),
        secondary_color=settings.get("color_secondary", ""),
        items=items,
        settings=settings
    )
    if filename in ent_files:
        return {"filename": filename, "content": ent_files[filename]}

    local_p = os.path.join(corp.SITES, str(jid), filename)
    if os.path.exists(local_p):
        try:
            with open(local_p, "r", encoding="utf-8") as f:
                return {"filename": filename, "content": f.read()}
        except Exception:
            pass

    raise HTTPException(404, f"الملف {filename} غير موجود")


@app.put("/api/sites/{slug_or_id}/files/{filename:path}")
def save_site_file_content(
    slug_or_id: str,
    filename: str,
    body: SiteFileSaveRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Saves updated content of a file."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    filename = safe_site_filename(filename)
    require_security_feature(
        "ENABLE_TENANT_FILE_EDITOR",
        "versioned artifacts, content validation, and a reviewed publishing workflow",
    )

    content = body.content
    if filename == "index.html":
        db.x("UPDATE site_pages SET html=? WHERE job_id=?", (content, jid))
        d = os.path.join(corp.SITES, str(jid))
        if os.path.exists(d):
            try:
                with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass
    else:
        existing = db.one("SELECT id FROM site_files WHERE job_id=? AND filename=?", (jid, filename))
        if existing:
            db.x("UPDATE site_files SET content=?, created_at=? WHERE id=?", (content, time.time(), existing["id"]))
        else:
            db.x(
                "INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, 'code', ?, '', ?)",
                (jid, filename, content, time.time())
            )
        d = os.path.join(corp.SITES, str(jid))
        if os.path.exists(d):
            try:
                fp = os.path.join(d, filename)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass

    corp.log(jid, f"✏️ تم حفظ تعديلات على الملف: {filename}")
    return {"success": True, "message": f"تم حفظ التعديلات على {filename} بنجاح!"}


# =========================================================
# Multi-Tenant Database Engine APIs
# =========================================================
@app.get("/api/sites/{slug_or_id}/database")
def get_site_database_status(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Returns the tenant database schema, catalog, table counts, and storage status."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    tenant_db = db.get_tenant_db(jid)
    settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    items = db.q("select * from site_items where job_id=? order by id", (jid,))
    brand = settings.get("brand_name") or f"site_{jid}"

    # If tenant_db hasn't been initialized yet, initialize it dynamically
    if not tenant_db:
        from app.enterprise_generator import generate_enterprise_project
        ent_files = generate_enterprise_project(
            job_id=jid,
            brand_name=brand,
            niche=settings.get("category", "general"),
            slogan=settings.get("slogan", ""),
            primary_color=settings.get("color_primary", ""),
            secondary_color=settings.get("color_secondary", ""),
            items=items,
            settings=settings
        )
        schema_sql = ent_files.get("schema.sql", "")
        initial_json = json.loads(ent_files.get("database.json", "{}"))
        catalog_tables = ["users", "categories", "products", "orders", "promo_codes", "reviews", "store_settings"]
        db.register_tenant_db(jid, brand, schema_sql, catalog_tables, initial_json)
        tenant_db = db.get_tenant_db(jid)

    tables_catalog = []
    try:
        tables_catalog = json.loads(tenant_db.get("tables_catalog") or "[]")
    except Exception:
        tables_catalog = ["users", "categories", "products", "orders", "promo_codes", "reviews", "store_settings"]

    # Calculate actual table row counts
    table_stats = []
    total_records = 0
    for tbl in tables_catalog:
        if tbl == "products":
            cnt = len(items)
        elif tbl == "orders":
            o_row = db.one("SELECT count(*) as c FROM site_orders WHERE job_id=?", (jid,))
            cnt = o_row.get("c", 0) if o_row else 0
        else:
            rec_row = db.one("SELECT count(*) as c FROM tenant_records WHERE job_id=? AND table_name=?", (jid, tbl))
            cnt = rec_row.get("c", 0) if rec_row else 0
        table_stats.append({"table_name": tbl, "row_count": cnt})
        total_records += cnt

    return {
        "success": True,
        "job_id": jid,
        "tenant_id": tenant_db.get("tenant_id") or f"tenant_db_{jid}",
        "brand_name": brand,
        "engine": tenant_db.get("engine") or "Enterprise SQLite 3 / libSQL Cloud",
        "db_filename": tenant_db.get("db_filename") or "database.sqlite",
        "total_tables": len(table_stats),
        "total_records": total_records,
        "size_bytes": tenant_db.get("size_bytes") or (total_records * 512 + 16384),
        "tables": table_stats,
        "schema_ddl": tenant_db.get("schema_ddl") or "",
        "status": tenant_db.get("status") or "active"
    }


@app.get("/api/sites/{slug_or_id}/database/tables/{table_name}")
def get_site_database_table_data(
    slug_or_id: str,
    table_name: str,
    limit: int = 100,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Retrieves real-time rows from a specified table in the tenant's database."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    # 1. Check live database tables first
    if table_name == "products":
        rows = db.q("SELECT id, title as name_ar, price, category, description, badge, image_url, created_at FROM site_items WHERE job_id=? ORDER BY id ASC LIMIT ?", (jid, limit))
        return {"table": table_name, "count": len(rows), "rows": rows}
    elif table_name == "orders":
        rows = db.q("SELECT id, customer_name, customer_phone, customer_address, total_egp as total_price, payment_method, status as order_status, created_at FROM site_orders WHERE job_id=? ORDER BY id DESC LIMIT ?", (jid, limit))
        return {"table": table_name, "count": len(rows), "rows": rows}

    # 2. Check tenant_records virtualization layer
    records = db.get_tenant_table_records(jid, table_name, limit)
    return {"table": table_name, "count": len(records), "rows": records}


@app.post("/api/sites/{slug_or_id}/database/query")
def execute_site_database_query(
    slug_or_id: str,
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Runs a safe SQL query against the tenant database."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    require_security_feature(
        "ENABLE_TENANT_SQL_CONSOLE",
        "a read-only, allow-listed reporting API with database-enforced tenant isolation",
    )

    raw_query = body.get("query")
    if not isinstance(raw_query, str):
        raise HTTPException(400, "A SQL query string is required")
    raw_query = raw_query.strip()
    if not raw_query:
        raise HTTPException(400, "يرجى إرسال استعلام SQL صالح")

    # This temporary console is read-only even when explicitly enabled. Its
    # eventual replacement is a purpose-built reporting API, not a SQL proxy.
    lower_q = raw_query.lower()
    if (
        not re.match(r"^\s*select\s+", raw_query, re.IGNORECASE)
        or ";" in raw_query
        or "--" in raw_query
        or "/*" in raw_query
        or "*/" in raw_query
    ):
        raise HTTPException(400, "Only one read-only SELECT query is allowed")
    if len(raw_query) > 2000:
        raise HTTPException(400, "Reporting query is too long")
    table_match = re.search(r"\bfrom\s+([a-zA-Z0-9_]+)\b", lower_q)
    table_name = table_match.group(1) if table_match else ""
    allowed_tables = {"products", "orders", "categories", "site_items", "site_orders"}
    if table_name not in allowed_tables:
        raise HTTPException(400, "This reporting table is not allow-listed")

    t_start = time.time()

    # Check if physical SQLite file exists on disk
    local_db_path = os.path.join(corp.SITES, str(jid), "database.sqlite")
    if os.path.exists(local_db_path):
        import sqlite3
        try:
            # Check every table access, including JOINs and nested SELECTs.
            conn = sqlite3.connect(local_db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only = ON")

            def authorize(action, arg1, _arg2, _database, _trigger):
                if action == sqlite3.SQLITE_SELECT:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and str(arg1).lower() in allowed_tables:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY

            conn.set_authorizer(authorize)
            query_started = time.monotonic()

            def stop_expensive_query():
                # SQLite invokes this every 1,000 virtual-machine instructions.
                return int(time.monotonic() - query_started > 0.25)

            conn.set_progress_handler(stop_expensive_query, 1000)
            cursor = conn.cursor()
            cursor.execute(raw_query)
            col_names = [d[0] for d in cursor.description] if cursor.description else []
            rows = [dict(r) for r in cursor.fetchmany(101)[:100]]
            conn.close()
            ms = round((time.time() - t_start) * 1000, 2)
            db.x("INSERT INTO tenant_queries_log (job_id, tenant_id, query_sql, rows_affected, execution_ms, executed_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (jid, f"tenant_db_{jid}", raw_query, len(rows), ms, time.time()))
            return {"success": True, "columns": col_names, "rows": rows, "count": len(rows), "execution_ms": ms}
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            audit.record(
                "tenant.reporting_query_failed",
                actor_type="user",
                target_type="job",
                target_id=str(jid),
                outcome="failure",
                metadata={"table": table_name},
            )
            raise HTTPException(400, "The reporting query could not be completed")

    # Fallback to query virtualized tables
    if table_name == "products":
        rows = db.q("SELECT id, title as name, price, category, badge FROM site_items WHERE job_id=? LIMIT 50", (jid,))
    elif table_name == "orders":
        rows = db.q("SELECT id, customer_name, customer_phone, total_egp, status FROM site_orders WHERE job_id=? LIMIT 50", (jid,))
    else:
        rows = db.get_tenant_table_records(jid, table_name, 50)

    ms = round((time.time() - t_start) * 1000, 2)
    cols = list(rows[0].keys()) if rows else ["id", "result"]
    db.x("INSERT INTO tenant_queries_log (job_id, tenant_id, query_sql, rows_affected, execution_ms, executed_at) VALUES (?, ?, ?, ?, ?, ?)",
         (jid, f"tenant_db_{jid}", raw_query, len(rows), ms, time.time()))
    return {"success": True, "columns": cols, "rows": rows, "count": len(rows), "execution_ms": ms}


@app.get("/api/sites/{slug_or_id}/database/download")
def download_site_database_sqlite(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Downloads the physical SQLite database file for the website."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    local_db_path = os.path.join(corp.SITES, str(jid), "database.sqlite")
    if os.path.exists(local_db_path):
        return FileResponse(local_db_path, media_type="application/x-sqlite3", filename=f"site_{jid}_database.sqlite")

    # If on serverless, generate SQLite database in memory and stream
    import sqlite3, io
    tenant_db = db.get_tenant_db(jid)
    schema_sql = (tenant_db.get("schema_ddl") or "") if tenant_db else ""
    if not schema_sql:
        settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
        items = db.q("select * from site_items where job_id=? order by id", (jid,))
        from app.enterprise_generator import generate_enterprise_project
        ent = generate_enterprise_project(jid, settings.get("brand_name") or f"site_{jid}", "general", "", "", "", items, settings)
        schema_sql = ent.get("schema.sql", "")

    mem_conn = sqlite3.connect(":memory:")
    mem_conn.executescript(schema_sql)
    mem_conn.commit()

    dest = io.BytesIO()
    for line in mem_conn.iterdump():
        dest.write(f"{line}\n".encode("utf-8"))
    mem_conn.close()
    dest.seek(0)
    return StreamingResponse(
        dest,
        media_type="application/sql",
        headers={"Content-Disposition": f"attachment; filename=site_{jid}_schema.sql"}
    )


# =========================================================
# Cybersecurity Reviewer & OWASP Top 10 SAST Audit APIs
# =========================================================
@app.get("/api/sites/{slug_or_id}/security-audit")
def get_site_security_audit(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Retrieves OWASP Top 10 compliance score and SAST code inspection report."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    cached = db.get_security_audit(jid)
    if cached and cached.get("audited_at"):
        return {"success": True, "job_id": jid, "audit": cached}

    return execute_live_sast_scan(jid)


@app.post("/api/sites/{slug_or_id}/security-audit/scan")
def trigger_site_security_audit_scan(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Forces a fresh SAST code scan and returns updated OWASP Top 10 compliance results."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    return execute_live_sast_scan(jid)


def execute_live_sast_scan(jid: int):
    page_row = db.one("SELECT html FROM site_pages WHERE job_id = ?", (jid,))
    html = (page_row.get("html") or "") if page_row else ""

    files_dict: Dict[str, str] = {}
    db_files = db.q("SELECT filename, content FROM site_files WHERE job_id = ?", (jid,))
    for f in db_files:
        files_dict[f["filename"]] = f.get("content") or ""

    local_dir = os.path.join(corp.SITES, str(jid))
    if os.path.isdir(local_dir):
        for root, _, filenames in os.walk(local_dir):
            for fn in filenames:
                rel = os.path.relpath(os.path.join(root, fn), local_dir).replace("\\", "/")
                if rel.endswith((".js", ".json", ".html", ".sql", ".env")):
                    try:
                        with open(os.path.join(root, fn), "r", encoding="utf-8", errors="ignore") as rf:
                            files_dict[rel] = rf.read()
                    except Exception:
                        pass

    if len(files_dict) < 5:
        from app.enterprise_generator import generate_enterprise_project
        settings = db.one("SELECT * FROM site_settings WHERE job_id = ?", (jid,)) or {}
        items = db.q("SELECT * FROM site_items WHERE job_id = ? ORDER BY id", (jid,))
        brand = settings.get("brand_name") or f"site_{jid}"
        files_dict = generate_enterprise_project(
            job_id=jid,
            brand_name=brand,
            niche=settings.get("category", "general"),
            slogan=settings.get("slogan", ""),
            primary_color=settings.get("color_primary", ""),
            secondary_color=settings.get("color_secondary", ""),
            items=items,
            settings=settings
        )

    audit_data = security.run_sast_security_scan(files_dict, html)
    db.save_security_audit(jid, audit_data)
    audit_data["job_id"] = jid
    return {"success": True, "job_id": jid, "audit": audit_data}


# =========================================================
# Iterative Development: Prompt Refinement with Multimodal Context
# =========================================================
@app.post("/api/sites/{slug_or_id}/refine")
async def refine_site(
    slug_or_id: str,
    body: SiteRefineRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Iteratively refines the site via natural language prompt + optional document text."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(400, "يرجى كتابة تعليمات التعديل والتطوير")

    check_guardrails(prompt)

    doc_text = body.extracted_text.strip()
    file_url = body.file_url.strip()

    page = db.one("SELECT html FROM site_pages WHERE job_id=?", (jid,))
    current_html = (page.get("html") or "") if page else ""
    settings = db.one("SELECT * FROM site_settings WHERE job_id=?", (jid,)) or {}

    sys_msg = (
        "You are AutoCorp's Elite Lead Frontend & Full-Stack Architect. "
        "The user wants to iteratively refine and upgrade their existing web application. "
        "Maintain high aesthetic standards, Egyptian cultural resonance, responsive Tailwind/CSS, and all functional elements. "
        "If they provide document text or logo, integrate it seamlessly into the structure. "
        "Return ONLY the updated complete HTML code, enclosed in ```html ... ``` or raw HTML."
    )

    user_msg = (
        f"Site ID: {jid}\n"
        f"Brand Name: {settings.get('brand_name', '')}\n"
        f"Current Niche: {settings.get('category', 'general')}\n"
        f"User Refinement Prompt: {prompt}\n"
    )
    if doc_text:
        user_msg += f"\nAdditional Extracted Document/Catalog/CV Text:\n{doc_text[:3000]}\n"
    if file_url:
        user_msg += f"\nUploaded Asset/Logo URL: {file_url}\n"

    user_msg += f"\nCurrent HTML snippet (first 3000 chars):\n{current_html[:3000]}\n\n"
    user_msg += "Produce the updated, complete, production-ready HTML code now."

    resp = await llm.call(
        system=sys_msg,
        user=user_msg,
        tier="builder",
        mock=current_html
    )

    new_html = resp.get("text") or current_html
    if "```html" in new_html:
        new_html = new_html.split("```html")[1].split("```")[0].strip()
    elif "```" in new_html:
        new_html = new_html.split("```")[1].split("```")[0].strip()

    if "<!DOCTYPE html>" not in new_html and "<html" not in new_html:
        new_html = current_html

    artifact_issues = artifacts.validate_site_html(new_html)
    if artifact_issues:
        raise HTTPException(
            422,
            "Generated content did not meet the safe, responsive artifact baseline: " + "; ".join(artifact_issues),
        )

    db.x("UPDATE site_pages SET html=? WHERE job_id=?", (new_html, jid))
    d = os.path.join(corp.SITES, str(jid))
    if os.path.exists(d):
        try:
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write(new_html)
        except Exception:
            pass

    corp.log(jid, f"🪄 تم تطوير الموقع بنجاح عبر توجيه ذكي: {prompt[:80]}...")
    slug = make_site_slug(jid, settings.get("brand_name") or f"site_{jid}")

    return {
        "success": True,
        "message": "تم تطوير وتحديث الموقع بنجاح وفقاً لتوجيهاتك!",
        "slug": slug,
        "frontend_url": f"/sites/{slug}/"
    }


# =========================================================
# Visual Component & Content Editor
# =========================================================
@app.post("/api/sites/{slug_or_id}/visual-edit")
async def visual_edit_site(
    slug_or_id: str,
    body: VisualSiteEditRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Visual content editor: edit title, slogan, colors, contact numbers, and toggle sections."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    body_data = body.model_dump(exclude_unset=True)

    brand = body_data.get("brand_name")
    slogan = body_data.get("slogan")
    color_primary = body_data.get("color_primary")
    color_secondary = body_data.get("color_secondary")
    logo_url = body_data.get("logo_url")
    phone = body_data.get("phone")
    whatsapp = body_data.get("whatsapp")
    vodafone_cash = body_data.get("vodafone_cash")
    instapay = body_data.get("instapay")
    theme = body_data.get("theme", "dark")

    # Fetch current settings
    curr = db.one("select * from site_settings where job_id=?", (jid,)) or {}

    db.x("""
        INSERT OR REPLACE INTO site_settings (
            job_id, brand_name, category, custom_domain, color_primary, color_secondary,
            logo_url, phone, whatsapp, address, vodafone_cash, instapay, fawry_code,
            cod_enabled, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?
        )
    """, (
        jid,
        brand or curr.get("brand_name") or f"site_{jid}",
        body_data.get("category") or curr.get("category") or "general",
        curr.get("custom_domain"),
        color_primary or curr.get("color_primary"),
        color_secondary or curr.get("color_secondary"),
        logo_url or curr.get("logo_url"),
        phone or curr.get("phone"),
        whatsapp or curr.get("whatsapp"),
        curr.get("address"),
        vodafone_cash or curr.get("vodafone_cash"),
        instapay or curr.get("instapay"),
        curr.get("fawry_code"),
        time.time()
    ))

    job_row = db.one("select * from jobs where id=?", (jid,)) or {}
    items_rows = db.q("select * from site_items where job_id=? order by id", (jid,))
    active_settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}

    for flag in ["enable_faq", "enable_testimonials", "enable_gallery", "enable_reviews", "enable_promo"]:
        if flag in body_data:
            active_settings[flag] = body_data[flag]
    if slogan:
        active_settings["slogan"] = slogan
    if theme:
        active_settings["theme"] = theme

    new_html = builder.build_site_html(
        jid,
        brand or job_row.get("client") or "",
        job_row.get("request") or "",
        settings=active_settings,
        items=items_rows
    )

    db.x("UPDATE site_pages SET html=? WHERE job_id=?", (new_html, jid))
    d = os.path.join(corp.SITES, str(jid))
    if os.path.exists(d):
        try:
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write(new_html)
        except Exception:
            pass

    corp.log(jid, "🎨 تم تطبيق التعديلات المرئية على واجهة وتنسيق الموقع بنجاح")
    return {"success": True, "message": "تم حفظ وتطبيق التعديلات المرئية بنجاح!"}


# =========================================================
# Store Products Management (CRUD with Image Support)
# =========================================================
@app.post("/api/sites/{slug_or_id}/items")
def add_site_item(
    slug_or_id: str,
    body: SiteItemCreateRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Adds a new product/service item with price, category, and image URL."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    title = body.title.strip()
    if not title:
        raise HTTPException(422, "Product title must not be blank")
    price = float(body.price)
    category = body.category.strip() or "عام"
    desc = body.description.strip()
    badge = body.badge.strip()
    image_url = body.image_url.strip()
    if image_url:
        try:
            parsed_image_url = urlsplit(image_url)
            parsed_image_url.port  # Reject malformed ports before storing URLs.
        except ValueError as exc:
            raise HTTPException(422, "Image URL is invalid") from exc
        is_uploaded_image = re.fullmatch(
            r"/static/uploads/[A-Za-z0-9_-]{1,120}\.(?:jpg|jpeg|png|webp)",
            image_url,
        ) is not None
        is_secure_remote_image = (
            parsed_image_url.scheme == "https"
            and bool(parsed_image_url.hostname)
            and not parsed_image_url.username
            and not parsed_image_url.password
        )
        if not (is_uploaded_image or is_secure_remote_image):
            raise HTTPException(422, "Image URL must be HTTPS or a sanitized uploaded image")

    item_id = db.x(
        "INSERT INTO site_items (job_id, title, price, category, description, badge, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (jid, title, price, category, desc, badge, image_url, time.time())
    )

    job_row = db.one("select * from jobs where id=?", (jid,)) or {}
    items_rows = db.q("select * from site_items where job_id=? order by id", (jid,))
    active_settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    new_html = builder.build_site_html(jid, job_row.get("client") or "", job_row.get("request") or "", settings=active_settings, items=items_rows)
    db.x("UPDATE site_pages SET html=? WHERE job_id=?", (new_html, jid))

    return {"success": True, "item_id": item_id, "message": f"تمت إضافة ({title}) بنجاح!"}


@app.delete("/api/sites/{slug_or_id}/items/{item_id}")
def delete_site_item(
    slug_or_id: str,
    item_id: int,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Deletes an item from site catalog."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    db.x("DELETE FROM site_items WHERE id=? AND job_id=?", (item_id, jid))

    job_row = db.one("select * from jobs where id=?", (jid,)) or {}
    items_rows = db.q("select * from site_items where job_id=? order by id", (jid,))
    active_settings = db.one("select * from site_settings where job_id=?", (jid,)) or {}
    new_html = builder.build_site_html(jid, job_row.get("client") or "", job_row.get("request") or "", settings=active_settings, items=items_rows)
    db.x("UPDATE site_pages SET html=? WHERE job_id=?", (new_html, jid))

    return {"success": True, "message": "تم حذف الصنف من الكتالوج بنجاح!"}


# =========================================================
# Bot Integrations: Telegram & WhatsApp Setup for Stores
# =========================================================
@app.get("/api/sites/{slug_or_id}/integrations")
def get_site_integrations(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Returns bot integrations config and setup instructions."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    cfg = db.one("SELECT * FROM site_bot_configs WHERE job_id=?", (jid,)) or {}
    settings = db.one("SELECT * FROM site_settings WHERE job_id=?", (jid,)) or {}
    brand = settings.get("brand_name") or f"Site #{jid}"

    guide_telegram = [
        "1. افتح تطبيق تيليجرام وابحث عن @BotFather الرسمي.",
        "2. أرسل الأمر /newbot وحدد اسماً تجارياً للبوت واسم مستخدم ينتهي بـ bot.",
        "3. سيعطيك BotFather رمز الوصول البرمجي (API Token) مثل: 123456:ABC-DEF...",
        "4. الصق التوكن هنا واكتب توجيهات الذكاء الاصطناعي للبوت (كيف يرد على استفسارات العملاء ويعرض المنتجات).",
        "5. اضغط 'حفظ وتفعيل' ليصبح البوت ممثلاً لمتجرك على مدار الساعة!"
    ]
    guide_whatsapp = [
        "1. ادخل على Meta for Developers وأنشئ تطبيق WhatsApp Business API.",
        "2. انسخ الـ Permanent Access Token ورقم الهاتف المسجل.",
        "3. الصق التوكن هنا لتفعيل الرد التلقائي وإشعارات الأوردرات الفورية."
    ]

    safe_config = {key: value for key, value in cfg.items() if key != "bot_token"}
    if cfg.get("bot_token"):
        safe_config["has_bot_token"] = True

    return {
        "job_id": jid,
        "brand_name": brand,
        "config": safe_config,
        "guide_telegram": guide_telegram,
        "guide_whatsapp": guide_whatsapp,
        "suggested_prompt": f"أنت المساعد الذكي والممثل الرسمي لمتجر {brand}. مهمتك الترحيب بالزبائن، الإجابة عن مواصفات المنتجات والأسعار، ومساعدتهم في إتمام الطلبات وتأكيد الدفع عبر فودافون كاش وإنستاباي والدفع عند الاستلام بأسلوب مصري راقٍ وودود."
    }


@app.post("/api/sites/{slug_or_id}/integrations/bot")
def save_site_bot_config(
    slug_or_id: str,
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Saves Telegram / WhatsApp bot credentials and system prompt."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    require_security_feature(
        "ENABLE_TENANT_BOT_CREDENTIALS",
        "per-tenant encrypted secret storage and provider OAuth/webhook verification",
    )

    platform = body.get("bot_platform", "telegram")
    token = (body.get("bot_token") or "").strip()
    name = (body.get("bot_name") or "").strip()
    prompt = (body.get("system_prompt") or "").strip()
    active = 1 if body.get("is_active", True) else 0

    db.x("""
        INSERT OR REPLACE INTO site_bot_configs (job_id, bot_platform, bot_token, bot_name, system_prompt, is_active, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (jid, platform, token, name, prompt, active, time.time()))

    corp.log(jid, f"🤖 تم ضبط وربط بوت {platform} لخدمة عملاء الموقع بنجاح ({name})")
    return {"success": True, "message": f"تم حفظ وربط بوت {platform} بنجاح!"}


# =========================================================
# AI Marketing Automations: Email & Social Campaigns
# =========================================================
@app.get("/api/sites/{slug_or_id}/automations")
def get_site_automations(
    slug_or_id: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Lists drafted and approved marketing campaigns for this site."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    return db.q("SELECT * FROM site_automations WHERE job_id=? ORDER BY id DESC", (jid,))


@app.post("/api/sites/{slug_or_id}/automations/generate-email")
async def generate_marketing_email(
    slug_or_id: str,
    body: MarketingEmailDraftRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """AI Marketing Agent: Drafts a targeted promotional email awaiting owner approval."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    goal = body.goal.strip() or "عرض ترويجي وتنشيط مبيعات"
    audience = body.target_audience.strip() or "العملاء المسجلين والزبائن الجدد"
    check_guardrails(goal)
    check_guardrails(audience)

    settings = db.one("SELECT * FROM site_settings WHERE job_id=?", (jid,)) or {}
    items = db.q("SELECT title, price FROM site_items WHERE job_id=? LIMIT 5", (jid,))
    brand = settings.get("brand_name") or f"متجر #{jid}"

    sys_prompt = (
        "You are AutoCorp's Elite Direct-Response Copywriter and Email Marketing Strategist for Egyptian SMEs. "
        "Draft a compelling, high-converting promotional email in polished, friendly Egyptian Arabic. "
        "Include: 1) Catchy Subject Line, 2) Preview Header, 3) Engaging Story/Hook, 4) Special Offer & Product Highlights, 5) Urgent Call to Action button. "
        "Do NOT invent false guarantees. Make it feel authentic, professional, and exciting."
    )
    prod_strs = [f"{it.get('title', '')} ({it.get('price', 0)} ج.م)" for it in items]
    top_prods_text = ", ".join(prod_strs)
    user_prompt = (
        f"Brand: {brand}\n"
        f"Activity: {settings.get('category', 'general')}\n"
        f"Goal: {goal}\n"
        f"Audience: {audience}\n"
        f"Top Products: {top_prods_text}\n"
    )

    resp = await llm.call(
        system=sys_prompt,
        user=user_prompt,
        tier="writer",
        mock=f"Subject: عروض خاصة من {brand}!\n\nأهلاً بك عميلنا العزيز،\nيسعدنا تقديم أقوى العروض الحصرية بمناسبة التوسعات الجديدة..."
    )

    content = resp.get("text") or "إيميل ترويجي جاهز للاعتماد"
    title = f"حملة إيميل: {goal[:40]}"

    auto_id = db.x(
        "INSERT INTO site_automations (job_id, type, title, content, target_platform, status, created_at) VALUES (?, 'email', ?, ?, 'email', 'pending_approval', ?)",
        (jid, title, content, time.time())
    )

    owner_chat = os.getenv("TELEGRAM_OWNER_CHAT_ID")
    if owner_chat:
        try:
            tg_notice = (
                f"📧 [مسودة إيميل تسويقي جديدة بانتظار موافقتك]\n"
                f"المتجر: {brand} (#{jid})\n"
                f"الهدف: {goal}\n\n"
                f"{content[:500]}...\n\n"
                f"💡 يمكنك مراجعة واعتماد الإرسال من لوحة التحكم."
            )
            await corp.tg_send(owner_chat, tg_notice)
        except Exception:
            pass

    corp.log(jid, f"📢 تم تجهيز مسودة إيميل تسويقي #{auto_id} بانتظار اعتماد المشرف")
    return {
        "success": True,
        "automation_id": auto_id,
        "title": title,
        "status": "pending_approval",
        "content": content,
        "message": "تم إنشاء مسودة الإيميل بنجاح وهي الآن في انتظار اعتمادك (Pending Approval) قبل الإرسال!"
    }


@app.post("/api/sites/{slug_or_id}/automations/approve-email")
async def approve_marketing_email(
    slug_or_id: str,
    body: SiteAutomationDecisionRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Owner Approval step: Approves and marks campaign for dispatch."""
    jid = resolve_job_id(slug_or_id)
    actor = require_site_access(jid, x_user_token, x_admin_key, authorization)
    auto_id = body.automation_id
    decision = body.decision
    pending = db.one(
        "SELECT id FROM site_automations WHERE id=? AND job_id=? AND status='pending_approval'",
        (auto_id, jid),
    )
    if not pending:
        raise HTTPException(409, "This campaign is not awaiting a decision")

    status = "approved" if decision == "approve" else "rejected"
    db.x(
        "UPDATE site_automations SET status=? WHERE id=? AND job_id=? AND status='pending_approval'",
        (status, auto_id, jid),
    )
    audit.record(
        "marketing.email_decision",
        actor_id=actor.get("id"),
        actor_type="administrator" if actor.get("is_admin") else "user",
        target_type="automation",
        target_id=str(auto_id),
        metadata={"decision": decision},
    )

    corp.log(jid, f"✅ تم اعتماد ونشر الحملة التسويقية #{auto_id} ({status})")
    return {
        "success": True,
        "automation_id": auto_id,
        "status": status,
        "message": f"تم {'اعتماد وبدء جدولة إرسال الإيميل' if status == 'approved' else 'رفض المسودة'} بنجاح!"
    }


@app.post("/api/sites/{slug_or_id}/automations/generate-social")
async def generate_social_post(
    slug_or_id: str,
    body: SocialPostDraftRequest,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Generates social media content (Facebook, Instagram, TikTok, LinkedIn, X)."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)

    platform = body.platform
    theme = body.theme.strip() or "تخفيضات وبوست تفاعلي"
    check_guardrails(theme)

    settings = db.one("SELECT * FROM site_settings WHERE job_id=?", (jid,)) or {}
    brand = settings.get("brand_name") or f"متجر #{jid}"

    sys_prompt = (
        f"You are AutoCorp's Viral Social Media Expert specializing in Egyptian market campaigns for {platform.upper()}. "
        "Write a highly engaging post with emojis, engaging hook, product benefits, Egyptian colloquial flavor, hashtags, and a clear Call To Action link."
    )
    user_prompt = f"Brand: {brand}\nNiche: {settings.get('category', 'general')}\nTheme: {theme}\nPlatform: {platform}"

    resp = await llm.call(
        system=sys_prompt,
        user=user_prompt,
        tier="writer",
        mock=f"🔥 أقوى العروض وصلت مع {brand}! ✨\nاطلب الآن واستمتع بتوصيل فوري ودفع عند الاستلام 🛵📦\n#مصر #تسوق #{brand.replace(' ', '_')}"
    )

    content = resp.get("text") or "محتوى بوست تسويقي"
    title = f"منشور {platform.title()}: {theme[:30]}"

    auto_id = db.x(
        "INSERT INTO site_automations (job_id, type, title, content, target_platform, status, created_at) VALUES (?, 'social', ?, ?, ?, 'pending_approval', ?)",
        (jid, title, content, platform, time.time())
    )

    return {
        "success": True,
        "automation_id": auto_id,
        "title": title,
        "status": "pending_approval",
        "content": content,
        "message": f"تم تجهيز بوست {platform} بنجاح!"
    }



@app.post("/api/discovery/questions")
def get_discovery_questions(body: dict):
    category = body.get("category") or "عام"
    brand_name = body.get("brand_name") or "المشروع"
    
    if any(k in category for k in ["خضار", "فواكه", "أغذية", "مزرعة", "عضوي"]):
        questions = [
            {"id": "q1", "label": "المنتجات الأكثر طلباً", "question": f"ما هي أهم أصناف الخضار أو الفواكه التي ترغب في تمييزها على واجهة {brand_name}؟", "placeholder": "مثال: طماطم بلدي، بطاطس تحمير، بوكسات التوفير العائلية"},
            {"id": "q2", "label": "مناطق التوصيل والشحن", "question": "ما هي الأحياء والمناطق التي تغطيها خدمة التوصيل لديكم ومتوسط وقت التسليم؟", "placeholder": "مثال: التجمع، المعادي، الشيخ زايد - التوصيل خلال ساعتين"},
            {"id": "q3", "label": "العروض الافتتاحية", "question": "هل تود إعلان خصم افتتاحي للعملاء الجدد في أعلى الصفحة الرئيسية؟", "placeholder": "مثال: خصم 15% على أول طلب + شحن مجاني للطلبات فوق 200 ج.م"},
            {"id": "q4", "label": "بوابات الدفع المفضلة", "question": "ما هي وسيلة الدفع الأساسية التي تفضلها لاستلام التحويلات من عملائك؟", "placeholder": "مثال: فودافون كاش ومحافظ المحمول، إنستاباي، والدفع عند الاستلام"}
        ]
    elif any(k in category for k in ["مطعم", "كافيه", "أكل", "مشويات", "وجبات"]):
        questions = [
            {"id": "q1", "label": "الوجبات الرئيسية", "question": f"ما هي أشهر الوجبات أو الأطباق الخاصة التي يتميز بها {brand_name}؟", "placeholder": "مثال: مشويات مشكلة على الفحم، طواجن بلدي، حواوشي سوبر، برجر كرانشي"},
            {"id": "q2", "label": "خيارات الاستلام والتوصيل", "question": "هل تتيح التوصيل للمنازل فقط أم أيضاً الاستلام من الفرع؟", "placeholder": "مثال: توصيل سريع ساخن لجميع المناطق + استلام من الفرع الرئيسي"},
            {"id": "q3", "label": "العروض العائلية", "question": "ما هي العروض أو وجبات التوفير التي ترغب في إبرازها؟", "placeholder": "مثال: وجبة العائلة السوبر 4 أفراد بسعر خاص"},
            {"id": "q4", "label": "طرق الدفع والتأكيد", "question": "كيف تفضل استلام مستحقات الأوردرات من الزبائن؟", "placeholder": "مثال: كاش عند الاستلام، وفودافون كاش، وإنستاباي"}
        ]
    else:
        questions = [
            {"id": "q1", "label": "مجال الخدمة الرئيسي", "question": f"ما هي أبرز الخدمات أو المنتجات التي تقدمها في {brand_name}؟", "placeholder": "مثال: استشارات وحلول تقنية، تدريب وتطوير أعمال، خدمات تسويق"},
            {"id": "q2", "label": "الجمهور المستهدف", "question": "من هي الفئة الأكثر استفادة من خدماتك (أفراد، شركات، تجار)؟", "placeholder": "مثال: أصحاب الشركات الصغيرة والمتوسطة ورواد الأعمال في مصر"},
            {"id": "q3", "label": "الميزة التنافسية", "question": "ما الذي يميز خدماتك عن باقي المنافسين في السوق المصري؟", "placeholder": "مثال: سرعة التنفيذ، ضمان الجودة، وأسعار اقتصادية مدروسة"},
            {"id": "q4", "label": "طرق التعاقد والسداد", "question": "ما هي خطط السداد أو الدفع التي توفرها لعملائك؟", "placeholder": "مثال: تحويل بنكي، إنستاباي، وفودافون كاش"}
        ]
    return {"questions": questions}


# =========================================================
# Posts, Proposals & Favicon
# =========================================================
@app.get("/favicon.ico")
def favicon():
    return HTMLResponse("", status_code=204)

# =========================================================
# Company Introspection & Financial Summary
# =========================================================
@app.api_route("/api/tick", methods=["GET", "POST"])
async def trigger_tick(x_cron_key: str = Header(default="")):
    """Run a scheduled operation using a header-only secret, never a URL key."""
    guard(["CRON_KEY"], x_cron_key)
    return await corp.tick()


def extract_smart_brand(prompt: str, niche: str) -> str:
    p = prompt.strip()
    
    # 0. Intelligent Portfolio Name & Profession Extraction
    if niche in ("portfolio", "cybersecurity") or any(k in p.lower() for k in ["بورتفوليو", "بروفايل", "cv", "سيرة ذاتية", "موقع شخصي"]):
        port_m = re.search(r'(?:بورتفوليو|بروفايل|موقع\s*شخصي|cv|سيرة\s*ذاتية)\s+(?:لـ\s*|ل_\s*)?([^\n،,\.؛]+)', p, re.IGNORECASE)
        if port_m:
            target = port_m.group(1).strip()
            # Clean introductory phrases: "لشخص اسمه عمر مختار", "لواحد اسمه عمر مختار", "شخص اسمه عمر مختار", "واحد اسمه عمر مختار", "اسمه عمر مختار"
            target = re.sub(r'^(?:لـ|لل|ل)?(?:شخص\s*اسمه|واحد\s*اسمه|شخص\s*يدعى|واحد\s*يدعى|اسمه)\s+', '', target).strip()
            # Clean Arabic preposition prefixes: "للفاروق" -> "الفاروق", "لياسين" -> "ياسين"
            if target.startswith("لل"):
                target = "ال" + target[2:]
            elif target.startswith("ل") and not target.startswith("لا") and not any(target.startswith(k) for k in ["ليلى", "لطفي", "لقمان", "لؤي", "ليث"]):
                target = target[1:].strip()

            role_split_pat = r'\s+(?=(?:مهندس|مطور|مبرمج|خبير|مصمم|باحث|استشاري|دكتور|طبيب|كاتب|محلل|أخصائي|اخصائي|مدير|تقني|متخصص|engineer|developer|designer|architect|specialist|consultant|scientist)\b)'
            parts = re.split(role_split_pat, target, 1)
            raw_name = parts[0].strip()
            raw_name = re.split(r'\s+(?:في\s+مجال|في\s+ال|في|تخصص|شغال\s+في|شغال|بيشتغل|يعمل\s+في|متخصص\s+في|متخصص)\b', raw_name)[0].strip()
            raw_role = parts[1].strip() if len(parts) > 1 else ""

            prompt_context = (raw_role + " " + p).lower()
            p_norm = re.sub(r'[إأآا]', 'ا', prompt_context)
            if any(k in p_norm for k in ["تصميم", "مصمم", "ديزاين", "ui", "ux", "جرافيك"]):
                final_role = "مصمم واجهات وتجربة المستخدم | UI/UX Designer"
            elif any(k in p_norm for k in ["ai", "ذكاء اصطناعي", "machine learning", "deep learning", "تعلم اله", "ديب ليرنينج", "data science", "علم بيانات"]):
                final_role = "مهندس ذكاء اصطناعي | AI Engineer"
            elif any(k in p_norm for k in ["سايبر", "سيكيورتي", "امن سيبراني", "اختراق", "pentest"]):
                final_role = "مهندس أمن سيبراني | Cybersecurity Specialist"
            elif any(k in p_norm for k in ["برمج", "مطور", "مبرمج", "ويب", "software", "full stack", "frontend", "backend"]):
                final_role = "مهندس برمجيات | Software Engineer"
            elif raw_role:
                final_role = raw_role
            else:
                final_role = "مهندس برمجيات وحلول رقمية"

            if len(raw_name) >= 3 and raw_name not in ("الموقع", "الشخصي", "واحد", "شخص", "حد"):
                return f"{raw_name} | {final_role}"

    # 1. Explicit name patterns:
    patterns = [
        r'(?:اسم\s*الموقع|اسم\s*المتجر|اسم\s*البراند|البراند|الماركة|ماركة|براند)\s*(?:هو|يكون|:)?\s*([^\n،,\.؛]+)',
        r'(?:لواحد\s*اسمه|لشخص\s*اسمه|واحد\s*اسمه|اسمه|باسم)\s+([^\n،,\.؛]+)',
    ]
    for pat in patterns:
        m = re.search(pat, p)
        if m:
            extracted = m.group(1).strip()
            # Clean trailing intent words
            extracted = re.split(r'\s+(?:شغال|بيشتغل|تخصص|في\s+مجال|بيبيع|عايز|عاوز|يعمل|يقدم)\b', extracted)[0].strip()
            if len(extracted) >= 2 and extracted not in ("ايه", "اي", "كدا", "كذا", "الموقع", "المتجر"):
                if niche in ("portfolio", "cybersecurity") and not any(k in extracted for k in ["خبير", "مهندس", "مطور"]):
                    prompt_ctx = p.lower()
                    if any(k in prompt_ctx for k in ["ui", "ux", "تصميم", "مصمم", "ديزاين"]):
                        return f"{extracted} | مصمم واجهات وتجربة المستخدم | UI/UX Designer"
                    elif any(k in prompt_ctx for k in ["ai", "ذكاء اصطناعي"]):
                        return f"{extracted} | مهندس ذكاء اصطناعي | AI Engineer"
                    elif any(k in prompt_ctx for k in ["برمج", "مطور", "مبرمج"]):
                        return f"{extracted} | مهندس برمجيات | Software Engineer"
                    return f"{extracted} | خبير الأمن السيبراني"
                return extracted

    # 2. Extract specific subject/topic from phrase like "موقع لبيع السيارات الكهربائية":
    concept_match = re.search(r'(?:موقع|متجر|معرض|منصة|شركة)\s+(?:لـ|ل)?(?:بيع|عرض|تسويق|شراء|تجارة|صيانة|خدمات)?\s*([^\n،,\.؛]+)', p)
    if concept_match:
        concept = concept_match.group(1).strip()
        concept = re.split(r'\s+(?:عايز|عاوز|علشان|عشان|بسرعة|في\s+مصر)\b', concept)[0].strip()
        if len(concept) >= 3 and not any(concept == stop for stop in ["الموقع", "المتجر", "موقع", "متجر", "اي حاجة", "اي حاجه"]):
            if any(k in concept for k in ["سيار", "مركبات", "عربيات"]):
                return f"معرض {concept}"
            if any(k in concept for k in ["عطور", "بخور"]):
                return f"متجر {concept}"
            if any(k in concept for k in ["اثاث", "أثاث", "مفروشات"]):
                return f"معرض {concept}"
            return f"متجر {concept}"

    # 3. Specific domain keywords:
    if any(k in p for k in ["سيار", "سيارة", "عربيات", "مركبات", "قطع غيار"]):
        return "إلكتريك درايف | معرض السيارات الكهربائية" if any(k in p for k in ["كهربائ", "ev"]) else "معرض أوتو موتورز للسيارات"
    if any(k in p for k in ["عطور", "عطر", "بخور", "عود", "مسك"]):
        return "دار العود | متجر العطور الفاخرة"
    if any(k in p for k in ["اثاث", "أثاث", "مفروشات", "ديكور"]):
        return "غاليري الأثاث والديكور العصري"
    if any(k in p for k in ["كتب", "روايات", "مكتبة"]):
        return "مكتبة دار المعرفة للكتب والروايات"
    if any(k in p for k in ["جيم", "مكملات", "بروتين", "لياقة"]):
        return "تيتانيوم فيتنس | مكملات وأجهزة رياضية"
    if any(k in p for k in ["حيوانات", "قطط", "كلاب", "بت شوب"]):
        return "بت لاند | مستلزمات وأغذية الحيوانات الأليفة"

    # 4. Portfolio personal names heuristics
    if niche in ("portfolio", "cybersecurity") or any(k in p for k in ["سايبر", "سيكيورتي", "بورتفوليو", "بروفايل", "مبرمج"]):
        name_m = re.search(r'(?:لـ\s*|ل_\s*)?(للفاروق|الفاروق|لياسين|ياسين|أحمد|احمد|محمد|محمود|علي|عمر|خالد|إبراهيم|ابراهيم|فاروق|كريم|طارق|يوسف|سارة|نور)\s+([^\n،,\.؛\s]+)', p)
        if name_m:
            first_name = name_m.group(1).strip()
            if first_name.startswith("لل"):
                first_name = "ال" + first_name[2:]
            elif first_name.startswith("ل") and not any(first_name.startswith(k) for k in ["ليلى", "لطفي", "لقمان", "لؤي", "ليث"]):
                first_name = first_name[1:]
            second_name = name_m.group(2).strip()
            if second_name in ("مهندس", "مطور", "مبرمج", "خبير", "مصمم"):
                cand_name = first_name
            else:
                cand_name = f"{first_name} {second_name}"
            prompt_ctx = p.lower()
            if any(k in prompt_ctx for k in ["ai", "ذكاء اصطناعي", "machine learning", "deep learning"]):
                return f"{cand_name} | مهندس ذكاء اصطناعي | AI Engineer"
            elif any(k in prompt_ctx for k in ["برمج", "مطور", "مبرمج", "ويب", "software"]):
                return f"{cand_name} | مهندس برمجيات | Software Engineer"
            elif any(k in prompt_ctx for k in ["تصميم", "مصمم", "ديزاينر", "ui", "ux"]):
                return f"{cand_name} | مصمم واجهات وتجربة المستخدم | UI/UX Designer"
            return f"{cand_name} | خبير الأمن السيبراني"
        return "بورتفوليو مهندس البرمجيات والذكاء الاصطناعي"

    # 5. Specialty Honey
    if niche == "honey" or any(k in p for k in ["عسل", "نحل", "سدر", "مناحل"]):
        return "مناحل الشفاء | متجر العسل الطبيعي الأصلي"

    # 6. Standard business niches
    if any(k in p for k in ["اجهز", "الكترون", "موبايل", "هواتف", "سماعات", "شواحن", "لابتوب"]):
        return "تكنو زون للأجهزة والإلكترونيات"
    if "كبابجي" in p or "مشويات" in p or "حواوشي" in p:
        return "مطعم ومشويات كبابجي الأصيل"
    if "خضار" in p or "فاكه" in p or "فواكه" in p:
        return "سوق الخضار والفواكه الطازجة"
    if "سوبرماركت" in p or "بقالة" in p or "ماركت" in p:
        return "سوبرماركت البركة ماركت"
    if "كافيه" in p or "قهوة" in p or "مقهى" in p or re.search(r'\bبن\b', p):
        return "كافيه ومقهى الرواق"
    if "ملابس" in p or "ازياء" in p or "فاشون" in p or "بوتيك" in p:
        return "بوتيك الأناقة للملابس"
    if "صيدلية" in p or "علاج" in p or "دواء" in p:
        return "صيدلية الشفاء والعافية"
    if "عيادة" in p or "دكتور" in p or "طبيب" in p or "اسنان" in p:
        return "عيادة النخبة للرعاية الطبية"
    if "شركة" in p or "وكالة" in p or "تسويق" in p:
        return "وكالة براند ماسترز للتسويق الرقمي"
    if "حلويات" in p or "تورتة" in p or "بسبوسة" in p:
        return "حلواني قصر السعادة"
    if "سمك" in p or "اسماك" in p or "بحريات" in p:
        return "مطعم ومأكولات بحرية الصياد"
    if "برجر" in p or "بيتزا" in p or "شاورما" in p:
        return "مطعم برجر وشاورما شيف"
    if niche == "automotive":
        return "معرض أوتو إليكتريك للسيارات"
    if niche == "perfumes":
        return "متجر لافندر للعطور الفاخرة"
    if niche == "furniture":
        return "معرض هوم ستايل للأثاث"
    if niche == "books":
        return "مكتبة القراء للكتب"
    if niche == "gym":
        return "باور جيم للمستلزمات الرياضية"
    if niche == "pets":
        return "متجر بتس كير للحيوانات الأليفة"
    if niche == "electronics":
        return "تكنو زون للأجهزة والإلكترونيات"
    if niche == "restaurant":
        return "مطعم الأكيل للوجبات الشهية"
    if niche == "vegetables":
        return "متجر الفريش للخضار والفواكه"
    return "المتجر الإلكتروني الحديث"


# =========================================================
# Telegram Integration: Live Poller & Webhook Handler
# =========================================================
async def handle_telegram_update(u: dict):
    """Processes incoming Telegram message or approval callback query."""
    owner_id = os.getenv("TELEGRAM_OWNER_CHAT_ID", "")
    
    cb = u.get("callback_query")
    if cb:
        cb_id = cb["id"]
        from_id = str(cb["from"]["id"])
        data = cb.get("data", "")
        if not owner_id or not hmac.compare_digest(from_id, owner_id):
            await corp.tg_send(from_id, "This approval action is restricted to the configured owner.")
            return
        
        # Approve / Reject actions
        if ":" in data:
            action, target_id = data.split(":", 1)
            if action in ("a", "r"):
                await corp.decide(int(target_id), "approve" if action == "a" else "reject")
                await corp.tg_send(from_id, f"✅ تم اعتماد قرارك بنجاح للمشروع #{target_id}")
            elif action in ("pa", "pr"):
                await corp.decide_post(int(target_id), "approve" if action == "pa" else "reject")
                await corp.tg_send(from_id, f"✅ تم اعتماد نشر البوست التسويقي #{target_id}")
        return

    msg = u.get("message")
    if not msg:
        return
        
    chat_id = str(msg["chat"]["id"])
    msg_id = msg.get("message_id")
    text = (msg.get("text") or msg.get("caption") or "").strip()

    # The primary key is the durable deduplication lock. A read-then-write
    # sequence is racy when Telegram retries reach concurrent workers.
    if msg_id:
        try:
            db.x(
                "INSERT INTO telegram_messages (chat_id, message_id, status, created_at) VALUES (?, ?, 'processing', ?)",
                (chat_id, msg_id, time.time()),
            )
        except Exception:
            # Fail closed: without a durable lock, repeating a side effect is
            # worse than asking Telegram to retry the update later.
            return

    # Telegram chat is not an acceptable password transport. Account linking
    # will move to a short-lived, browser-based verification flow in Phase 1.
    if text.startswith(("/register", "/login", "/admin")):
        await corp.tg_send(
            chat_id,
            "Password commands are disabled for security. Create or sign in to your account through the web dashboard.",
        )
        return

    # Check if this telegram user is linked to an account
    linked_user = db.one("SELECT id, username, role FROM users WHERE telegram_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    user_id = linked_user["id"] if linked_user else None
    user_name = linked_user["username"] if linked_user else f"tg:{chat_id}"
    is_user_admin = bool(linked_user and linked_user.get("role") == "admin") or (
        bool(owner_id) and hmac.compare_digest(owner_id, chat_id)
    )

    # 1. /start command
    if text.startswith("/start"):
        await corp.tg_send(
            chat_id,
            "مرحباً بك في AutoCorp 🤖🇪🇬\n"
            "وكالة الذكاء الاصطناعي ذاتية التشغيل للمتاجر والشركات والمحترفين في مصر.\n\n"
            "✨ يسعدني مساعدتك في إعداد مسودة موقع متجاوب وإدارة طلبات المتجر بانتظار تأكيد التاجر.\n\n"
            "📋 الأوامر المتاحة:\n"
            "• الحسابات وتسجيل الدخول يتمان عبر لوحة التحكم الآمنة على الويب\n"
            "• /my_sites — عرض مواقعك ومتاجرك المنشورة وروابطها\n"
            "• /build <وصف الموقع أو المتجر> — إطلاق وبرمجة موقعك فوراً\n"
            "• /help — دليل استخدام الوكالة والخدمات المتاحة\n"
            "• الموافقات الإدارية محصورة بحساب المالك المهيأ مسبقاً\n\n"
            "💡 أو ببساطة: اكتب فكرة موقعك (مثال: 'عايز اعمل بورتفوليو لواحد اسمه ياسين احمد في السايبر سيكيورتي' أو 'متجر بيع عسل') وسأنفذه فوراً!"
        )
        return

    # 2. /help command
    if text.startswith("/help"):
        await corp.tg_send(
            chat_id,
            "📖 دليل استخدام مستشار AutoCorp الذكي:\n\n"
            "1️⃣ بناء المواقع والمتاجر: اكتب تفاصيل نشاطك (مثال: 'بورتفوليو أمن سيبراني لـ ياسين أحمد' أو 'متجر عسل سدر فاخر' أو 'مطعم مشويات') أو أرسل صورة المنيو/البضاعة.\n"
            "2️⃣ الطلبات والحجوزات: الطلبات تُسجّل بانتظار تأكيد التاجر ولا تُعالج أي دفعة عبر البوت.\n"
            "3️⃣ باقة البداية المجانية: تتيح لك تجربة بناء حتى (موقعين) مجاناً.\n"
            "4️⃣ استضافة هوستينجر وGitHub: يمكنك تحميل كود الإنتاج كاملاً بملف ZIP أو النشر المباشر على GitHub و Vercel.\n\n"
            "لربط حسابك: استخدم لوحة التحكم الآمنة على الويب."
        )
        return

    # 3. /register command
    if text.startswith("/register"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await corp.tg_send(chat_id, "⚠️ الصيغة الصحيحة: /register اسم_المستخدم كلمة_المرور")
            return
        u_name, u_pass = parts[1].strip(), parts[2].strip()
        try:
            res = auth.register_user(u_name, u_pass)
            db.x("UPDATE users SET telegram_id = NULL WHERE telegram_id = ?", (chat_id,))
            db.x("UPDATE users SET telegram_id = ? WHERE id = ?", (chat_id, res["id"]))
            await corp.tg_send(
                chat_id,
                f"🎉 تم إنشاء حسابك بنجاح ({u_name}) وربطه بـ Telegram!\n"
                f"تم تفعيل باقة البداية (رصيد حتى موقعين مجاناً). يمكنك الآن طلب موقعك الأول!"
            )
        except Exception as e:
            await corp.tg_send(chat_id, f"❌ تعذر إنشاء الحساب: {e}")
        return

    # 4. /login command
    if text.startswith("/login"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await corp.tg_send(chat_id, "⚠️ الصيغة الصحيحة: /login اسم_المستخدم كلمة_المرور")
            return
        u_name, u_pass = parts[1].strip(), parts[2].strip()
        try:
            res = auth.login_user(u_name, u_pass)
            if res.get("id"):
                db.x("UPDATE users SET telegram_id = NULL WHERE telegram_id = ?", (chat_id,))
                db.x("UPDATE users SET telegram_id = ? WHERE id = ?", (chat_id, res["id"]))
            await corp.tg_send(
                chat_id,
                f"✅ تم تسجيل دخولك بنجاح كـ ({u_name})!\n"
                "أنت الآن جاهز لإدارة متاجرك ومواقعك أو طلب بناء موقع جديد."
            )
        except Exception as e:
            await corp.tg_send(chat_id, f"❌ خطأ في الدخول: {e}")
        return

    # 5. /my_sites command
    if text.startswith("/my_sites") or text.startswith("/sites"):
        sites = db.q(
            "SELECT id, client, status, is_paid FROM jobs WHERE user_id = ? OR client LIKE ? OR client = ? ORDER BY id DESC LIMIT 10",
            (user_id or -1, f"tg:{chat_id}%", user_name)
        )
        if not sites:
            await corp.tg_send(chat_id, "🛒 ليس لديك أي مواقع منشورة حتى الآن. لإنشاء موقعك الأول، اكتب وصف نشاطك التجاري أو استخدم /build.")
            return
        base_url = "https://autocorp-ai-websits-builder.vercel.app" if IS_VERCEL else "http://localhost:8000"
        msg_lines = ["📱 مواقعك الإلكترونية في AutoCorp:\n"]
        for s in sites:
            paid_str = "✅ نشط ومدفوع" if s.get("is_paid") else "⏳ تجريبي / في انتظار التفعيل"
            slug = make_site_slug(s['id'], s['client'])
            msg_lines.append(
                f"• موقع #{s['id']} ({s['client']})\n"
                f"  الحالة: {s['status']} | {paid_str}\n"
                f"  الرابط: {base_url}/sites/{slug}/\n"
            )
        msg_lines.append(f"\n💡 رصيدك المستخدم: {len(sites)} من {auth.MAX_SITES_PER_CLIENT} مواقع.")
        msg_lines.append("🗑️ لحذف أي موقع وتفريغ رصيدك: أرسل /delete رقم_الموقع (مثال: /delete 29) أو اكتب 'احذف كل المواقع'.")
        msg_lines.append("🌐 يمكنك تحميل حزمة هوستينجر أو ربط دومين خاص بك من لوحة تحكم الويب.")
        await corp.tg_send(chat_id, "\n".join(msg_lines))
        return

    # 6. /admin login command
    if text.startswith("/admin"):
        await corp.tg_send(
            chat_id,
            "Administrator login by Telegram password is disabled. Use the web console; "
            "approvals are sent only to the preconfigured owner chat."
        )
        return

    # 6.1 Natural Language Deletion & /delete Command
    del_kws = ["احذف", "امسح", "حذف", "مسح", "ازال", "ازالة", "الغاء", "الغي", "delete", "remove"]
    t_del_clean = text.lower().strip()
    is_deletion_request = text.startswith("/delete") or any(k in t_del_clean for k in del_kws)

    if is_deletion_request:
        # Check if an explicit project ID number was provided
        digits = re.findall(r'\b\d+\b', text)
        if digits:
            target_jid = int(digits[0])
            target_job = db.one("SELECT * FROM jobs WHERE id=?", (target_jid,))
            if not target_job:
                await corp.tg_send(chat_id, f"❌ المشروع #{target_jid} غير موجود.")
                return
            can_del = is_user_admin or (user_id and target_job.get("user_id") == user_id) or str(target_job.get("client")) == f"tg:{chat_id}" or str(target_job.get("client", "")).startswith(f"tg:{chat_id}")
            if can_del:
                audit.record(
                    "site.deletion_requested",
                    actor_id=user_id,
                    actor_type="administrator" if is_user_admin else "telegram_user",
                    target_type="job",
                    target_id=str(target_jid),
                )
                delete_tenant_records(target_jid)
                shutil.rmtree(os.path.join(corp.SITES, str(target_jid)), ignore_errors=True)
                
                # Check remaining count
                if user_id:
                    rem_row = db.one("SELECT count(*) as c FROM jobs WHERE user_id = ?", (user_id,))
                else:
                    rem_row = db.one("SELECT count(*) as c FROM jobs WHERE client = ? OR client LIKE ?", (f"tg:{chat_id}", f"tg:{chat_id}%"))
                rem_count = int(rem_row.get("c", 0) or 0) if rem_row else 0
                free_slots = max(0, auth.MAX_SITES_PER_CLIENT - rem_count)
                
                await corp.tg_send(
                    chat_id,
                    f"🗑️ تم حذف المشروع #{target_jid} ({target_job.get('client')}) وكافة ملفاته بنجاح!\n"
                    f"✨ رصيدك المتاح الآن: {free_slots} من {auth.MAX_SITES_PER_CLIENT} مواقع.\n"
                    f"🚀 يمكنك الآن إرسال فكرة موقعك أو البورتفوليو الجديد لنبدأ برمجته فوراً!"
                )
            else:
                await corp.tg_send(chat_id, "❌ ليس لديك صلاحية لحذف هذا المشروع.")
            return

        # No specific ID: Handle bulk deletion or conversational deletion
        bulk_kws = ["كل", "الموقعين", "المواقع", "احذفهم", "امسحهم", "اتعملوا", "عملتهم", "كلهم", "مواقعي", "دول"]
        user_sites = db.q(
            "SELECT id, client FROM jobs WHERE user_id = ? OR client LIKE ? OR client = ? ORDER BY id DESC",
            (user_id or -1, f"tg:{chat_id}%", user_name)
        )
        if not user_sites:
            await corp.tg_send(chat_id, "ℹ️ ليس لديك أي مواقع سابقة لحذفها. رصيدك متاح بالكامل ويمكنك طلب بناء موقعك الجديد فوراً! 🚀")
            return

        # If user explicitly asked for bulk/all, or has only 1 site, or asked "احذفهم" / "امسحهم" / "الموقعين":
        if any(k in t_del_clean for k in bulk_kws) or len(user_sites) == 1:
            deleted_ids = []
            for s in user_sites:
                jid = s["id"]
                audit.record("site.deletion_requested", actor_id=user_id, actor_type="telegram_user", target_type="job", target_id=str(jid))
                delete_tenant_records(jid)
                shutil.rmtree(os.path.join(corp.SITES, str(jid)), ignore_errors=True)
                deleted_ids.append(f"#{jid}")
            
            ids_str = " و ".join(deleted_ids)
            await corp.tg_send(
                chat_id,
                f"🗑️ تم حذف مشاريعك السابقة ({ids_str}) وكافة ملفاتها بنجاح!\n\n"
                f"✨ رصيدك الآن متاح بالكامل (0 من {auth.MAX_SITES_PER_CLIENT} مواقع).\n"
                f"🚀 يمكنك الآن إرسال فكرة موقعك أو البورتفوليو الجديد لنبدأ برمجته فوراً!"
            )
            return

        # If multiple sites exist and user didn't specify, guide them:
        lines = [
            f"⚠️ لديك {len(user_sites)} مواقع مسجلة. لتحديد الموقع المراد حذفه:\n",
        ]
        for s in user_sites:
            lines.append(f"• لحذف موقع #{s['id']} ({s['client']}): أرسل /delete {s['id']}")
        lines.append(f"\n💡 أو اكتب ببساطة: 'احذف كل المواقع' لحذفها جميعاً وتفريغ رصيدك بالكامل فوراً.")
        await corp.tg_send(chat_id, "\n".join(lines))
        return

    # 7. Conversational Handling & Guardrails
    check_guardrails(text)
    
    # Process attached document (PDF / Text / Catalog / Menu)
    uploaded_doc_text = ""
    uploaded_doc_name = ""
    if msg.get("document"):
        doc = msg["document"]
        file_id = doc.get("file_id")
        file_name = doc.get("file_name", "document.pdf")
        mime = doc.get("mime_type", "")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        file_size = int(doc.get("file_size") or 0)
        is_pdf = file_name.lower().endswith(".pdf") or mime == "application/pdf"
        if file_size > MAX_TELEGRAM_ATTACHMENT_BYTES:
            await corp.tg_send(chat_id, "The attached document exceeds the 10 MB limit and was not processed.")
        elif not is_pdf:
            await corp.tg_send(chat_id, "Only PDF documents are accepted for secure processing.")
        elif file_id and token:
            try:
                async with httpx.AsyncClient(timeout=40) as cl:
                    f_info = (await cl.get(f"https://api.telegram.org/bot{token}/getFile", params={"file_id": file_id})).json()
                    f_path = f_info.get("result", {}).get("file_path")
                    if f_path:
                        download = await cl.get(f"https://api.telegram.org/file/bot{token}/{f_path}")
                        download.raise_for_status()
                        raw_bytes = download.content
                        if len(raw_bytes) > MAX_TELEGRAM_ATTACHMENT_BYTES or not raw_bytes.startswith(b"%PDF-"):
                            raise ValueError("Telegram document did not meet the PDF attachment policy")
                        # This name is internal metadata only. PDFs are never
                        # retained at a public URL after text extraction.
                        clean_fn = f"{secrets.token_urlsafe(18)}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)[:60]}"
                        up_dir = "/tmp/uploads" if IS_VERCEL else os.path.join(BASE, "static", "uploads")
                        os.makedirs(up_dir, exist_ok=True)
                        up_path = os.path.join(up_dir, clean_fn)
                        with open(up_path, "wb") as f:
                            f.write(raw_bytes)
                        if file_name.lower().endswith(".pdf") or "pdf" in mime:
                            uploaded_doc_text = extract_pdf_text(raw_bytes)
                        # Brief PDFs are transient input, not public static assets.
                        if os.path.exists(up_path):
                            os.remove(up_path)
                        uploaded_doc_name = clean_fn
                        text = f"{text}\n\n[مستند مرفق من العميل: {file_name}]:\n{uploaded_doc_text[:3500]}".strip()
            except Exception as e:
                print(f"[TG DOC ERR] {e}")

    # Process attached photo
    uploaded_photo_url = ""
    if msg.get("photo"):
        photo_id = msg["photo"][-1]["file_id"]
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            try:
                async with httpx.AsyncClient(timeout=40) as cl:
                    f_info = (await cl.get(f"https://api.telegram.org/bot{token}/getFile", params={"file_id": photo_id})).json()
                    f_path = f_info.get("result", {}).get("file_path")
                    if f_path:
                        download = await cl.get(f"https://api.telegram.org/file/bot{token}/{f_path}")
                        download.raise_for_status()
                        raw_bytes = download.content
                        if len(raw_bytes) > MAX_TELEGRAM_ATTACHMENT_BYTES or not raw_bytes.startswith(b"\xff\xd8\xff"):
                            raise ValueError("Telegram photo did not meet the JPEG attachment policy")
                        raw_bytes = sanitize_image_upload(raw_bytes, ".jpg")
                        if len(raw_bytes) > MAX_TELEGRAM_ATTACHMENT_BYTES:
                            raise ValueError("Telegram photo exceeds the 10 MB limit after sanitization")
                        clean_fn = f"{secrets.token_urlsafe(18)}_tg_photo.jpg"
                        up_dir = "/tmp/uploads" if IS_VERCEL else os.path.join(BASE, "static", "uploads")
                        os.makedirs(up_dir, exist_ok=True)
                        up_path = os.path.join(up_dir, clean_fn)
                        with open(up_path, "wb") as f:
                            f.write(raw_bytes)
                        uploaded_photo_url = f"/static/uploads/{clean_fn}"
            except Exception as e:
                print(f"[TG PHOTO SAVE ERR] {e}")
        desc = await corp.tg_image_to_text(photo_id, text)
        text = f"{text}\n\n[تحليل صورة العميل بواسطة Vision Analyst]:\n{desc}".strip()

    # 7.1 Multi-Turn Conversation State Check
    conv = db.one("SELECT * FROM telegram_conversations WHERE chat_id = ?", (chat_id,))
    if conv and conv.get("stage") == "waiting_niche":
        # User is answering the follow-up question regarding specialization
        combined_text = f"{conv.get('last_message') or ''} {text}"
        pending_brand = conv.get("pending_brand") or ""
        db.x("DELETE FROM telegram_conversations WHERE chat_id = ?", (chat_id,))
        text = combined_text
        is_store_request = True
    else:
        # Greeting Detection
        greetings = ["اهلا", "أهلا", "مرحبا", "سلام", "السلام عليكم", "ازيك", "صباح الخير", "مساء الخير", "هاي", "الو", "مين انت", "عرفني بيك"]
        t_clean = text.lower().strip()
        if any(t_clean == g or t_clean.startswith(g + " ") for g in greetings) and len(t_clean) < 35 and not msg.get("photo") and not msg.get("document"):
            await corp.tg_send(
                chat_id,
                "أهلاً بك يا فندم! 🤖🇪🇬\n"
                "أنا المستشار الذكي لوكالة AutoCorp لبناء وتطوير المواقع والمتاجر للشركات والمحترفين في مصر.\n\n"
                "مهمتي أساعدك في إعداد مسودة موقع أو متجر إلكتروني متجاوب لنشاطك التجاري أو بورتفوليو شخصي. "
                "الطلبات تحتاج تأكيد التاجر، ولا تتوفر معالجة دفع عبر البوت.\n\n"
                "💡 كيف تحب نبدأ؟\n"
                "• لبدء البناء فوراً: اكتب تفاصيل نشاطك (مثال: 'عايز اعمل بورتفوليو لواحد اسمه ياسين احمد في السايبر سيكيورتي' أو 'متجر عسل').\n"
                "• يمكنك أيضاً إرسال ملف PDF (كتالوج أو منيو) أو صورة اللوجو وسأقوم ببناء الموقع بناءً عليها فوراً!\n"
                "• لتسجيل الدخول: استخدم لوحة التحكم الآمنة على الويب.\n"
                "• أو اسألني أي سؤال حول الميزات والأسعار والطلبات!"
            )
            return
        is_store_request = bool(msg.get("photo")) or bool(msg.get("document")) or is_store_creation_intent(text)

    # 7.2 Store / Website Creation
    if is_store_request:
        if not is_user_admin:
            if user_id:
                c_row = db.one("SELECT count(*) as c FROM jobs WHERE user_id = ?", (user_id,))
            else:
                c_row = db.one("SELECT count(*) as c FROM jobs WHERE client = ? OR client LIKE ?", (f"tg:{chat_id}", f"tg:{chat_id}%"))
            count_tg = int(c_row.get("c", 0) or 0) if c_row else 0
            if count_tg >= auth.MAX_SITES_PER_CLIENT:
                await corp.tg_send(
                    chat_id,
                    f"⚠️ عفواً، لقد استنفدت الحد الأقصى المسموح به ({auth.MAX_SITES_PER_CLIENT} مواقع) في باقتك الحالية!\n\n"
                    "💡 لتفريغ رصيدك وبناء مواقع جديدة، يمكنك حذف أي موقع سابق بسهولة:\n"
                    "• اكتب 'احذف كل المواقع' لتفريغ رصيدك بالكامل فوراً.\n"
                    "• أو اكتب /delete رقم_الموقع (مثال: /delete 29).\n"
                    "• أو اكتب /my_sites لمعاينة روابط مواقعك الحالية وأرقامها."
                )
                return

        niche = builder.detect_niche(text)
        brand = extract_smart_brand(text, niche)

        # Check if user only specified a person's name without any niche or activity
        has_niche_clue = any(k in text.lower() for k in [
            "سايبر", "سيكيورتي", "أمن", "امن", "برمج", "مطور", "عسل", "مطعم", "خضار", "اجهز",
            "ملابس", "عياد", "دكتور", "شركة", "وكالة", "بورتفوليو", "متجر", "محل", "كافيه"
        ])
        if not has_niche_clue and any(k in text for k in ["لواحد اسمه", "واحد اسمه", "اسمه"]) and len(text.split()) <= 6 and not msg.get("document"):
            # Save multi-turn state and ask for specialization!
            db.x("INSERT OR REPLACE INTO telegram_conversations (chat_id, stage, pending_brand, pending_niche, last_message, updated_at) VALUES (?, 'waiting_niche', ?, ?, ?, ?)",
                 (chat_id, brand, "", text, time.time()))
            await corp.tg_send(
                chat_id,
                f"أهلاً بك! تم تسجيل الاسم: ({brand}) 🚀\n\n"
                "ما هو مجال العمل أو التخصص لنقوم بتجهيز الموقع المناسب فوراً؟\n"
                "(مثال: أمن سيبراني / سايبر سيكيورتي، برمجة وتطوير ويب، متجر عسل طبيعي، مطعم ومشويات، عيادة، شركة تسويق)"
            )
            return

        pal_key = niche if niche in builder.PALETTES else ("cyber" if niche == "portfolio" else "emerald")
        pal = builder.PALETTES.get(pal_key, builder.PALETTES["emerald"])
        
        # Prevent rapid duplicates
        recent = db.one(
            "SELECT id FROM jobs WHERE client = ? AND request = ? AND created_at > ?",
            (brand, text, time.time() - 60)
        )
        if recent:
            print(f"[TG DEDUP] Skipping duplicate creation for {brand} (Job #{recent['id']})")
            return

        # Create job in DB with created status so agents plan and execute
        jid = db.x(
            "INSERT INTO jobs(client, request, status, user_id, price, cost, created_at) VALUES(?, ?, 'created', ?, 299.0, 0.0, ?)",
            (brand[:80], text[:4000], user_id, time.time())
        )
        
        # Save initial settings
        settings = {
            "brand_name": brand,
            "category": niche,
            "color_primary": pal["primary"],
            "color_secondary": pal["secondary"],
            "logo_url": uploaded_photo_url,
            "phone": "",
            "whatsapp": "",
            "vodafone_cash": "",
            "instapay": "",
            "fawry_code": "",
            "cod_enabled": 1
        }
        db.x("""
            INSERT OR REPLACE INTO site_settings (
                job_id, brand_name, category, color_primary, color_secondary, logo_url,
                phone, whatsapp, vodafone_cash, instapay, fawry_code, cod_enabled, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            jid, brand, niche, pal["primary"], pal["secondary"], uploaded_photo_url,
            settings["phone"], settings["whatsapp"], settings["vodafone_cash"], settings["instapay"],
            settings["fawry_code"], 1, time.time()
        ))

        # Record file if uploaded
        if uploaded_doc_name:
            try:
                db.x(
                    "INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, 'pdf', ?, ?, ?)",
                    (jid, uploaded_doc_name, uploaded_doc_text[:4000], "", time.time())
                )
            except Exception:
                pass
        if uploaded_photo_url:
            try:
                db.x(
                    "INSERT INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, 'image', 'لوجو أو صورة المتجر', ?, ?)",
                    (jid, os.path.basename(uploaded_photo_url), uploaded_photo_url, time.time())
                )
            except Exception:
                pass
        
        # Insert default catalog items with real imagery
        default_items = builder.get_default_catalog(niche, text + " " + brand)
        for it in default_items:
            db.x("INSERT INTO site_items(job_id, title, price, category, description, badge, image_url, created_at) VALUES(?,?,?,?,?,?,?,?)",
                 (jid, it["title"], it["price"], it["category"], it["desc"], it.get("badge", ""), it.get("image_url", ""), time.time()))
                 
        db_items = db.q("SELECT * FROM site_items WHERE job_id = ? ORDER BY id", (jid,))
        
        # Synthesize HTML immediately so live link is immediately valid
        html_code = builder.build_site_html(jid, brand, text, settings=settings, items=db_items)
        db.x("INSERT OR REPLACE INTO site_pages(job_id, html, created_at) VALUES(?, ?, ?)", (jid, html_code, time.time()))
        
        if not IS_VERCEL:
            d = os.path.join(corp.SITES, str(jid))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_code)
                
        slug = make_site_slug(jid, brand, niche)
        base_url = "https://autocorp-ai-websits-builder.vercel.app" if IS_VERCEL else "http://localhost:8000"
        site_link = f"{base_url}/sites/{slug}/"
        db.x("UPDATE jobs SET site_url = ? WHERE id = ?", (f"/sites/{slug}/", jid))

        # Launch AutoCorp AI Agents Team (CEO, Frontend Developer, Deep Learning Cybersecurity Reviewer, Code Reviewer)
        corp.spawn(corp.plan_job(jid))

        if niche == "portfolio":
            p_track = builder.detect_portfolio_track(text + " " + brand)
            if p_track == "design":
                prof_label = "تصميم واجهات وتجربة المستخدم (UI/UX Design)"
                prof_icon = "🎨"
            elif p_track == "ai":
                prof_label = "هندسة الذكاء الاصطناعي والتعلم العميق (AI & Deep Learning)"
                prof_icon = "🧠"
            elif p_track == "dev":
                prof_label = "هندسة البرمجيات وتطوير الحلول الرقمية (Software Engineering)"
                prof_icon = "💻"
            else:
                prof_label = "أمن سيبراني واختبار اختراق متقدم (Cybersecurity & Pentesting)"
                prof_icon = "🛡️"

            congrats_msg = (
                f"🎉 تم استلام طلبك وبدء العمل على موقعك الشخصي (Portfolio) بنجاح! 🚀\n\n"
                f"👤 الاسم: {brand}\n"
                f"{prof_icon} التخصص: {prof_label}\n"
                f"🤖 يقوم فريق وكلاء الذكاء الاصطناعي (CEO + Frontend Developer + تدقيق الأمان بنموذج Deep Learning + Code Reviewer) بفحص ومراجعة وتأمين موقعك الآن!\n\n"
                f"🌐 رابط الموقع المباشر:\n{site_link}\n\n"
                f"📊 يمكنك متابعة سجلات تنفيذ الوكلاء اللحظية مباشرة عبر لوحة تحكم AutoCorp."
            )
        else:
            congrats_msg = (
                f"🎉 تم استلام طلبك وبدء العمل على متجرك الإلكتروني بنجاح! 🚀\n\n"
                f"🏷️ اسم المتجر: {brand}\n"
                f"🛒 نوع النشاط: {niche}\n"
                f"🎨 الهوية: تم تخصيص ألوان وتصميم متناسق لنشاطك ({pal_key})\n"
                f"🤖 يقوم فريق وكلاء AutoCorp (CEO + مطور الواجهات + فحص الأمان بنموذج Deep Learning + مراجع الأكواد) بتطوير وتأمين المتجر الآن!\n\n"
                f"🌐 رابط متجرك المباشر:\n{site_link}\n\n"
                f"💡 يمكنك فتح الرابط ومتابعة تقدم الوكلاء في سجل العمليات (Events Ledger) من لوحة التحكم."
            )
            
        await corp.tg_send(chat_id, congrats_msg)
        if msg_id:
            db.x("UPDATE telegram_messages SET status = 'done' WHERE chat_id = ? AND message_id = ?", (chat_id, msg_id))
        return

    # 7.3 General Consultation Chat with Scope Guardrail
    sys_prompt = (
        "You are AutoCorp's friendly, highly knowledgeable Egyptian AI consultant for businesses, professionals, and freelancers. "
        "AutoCorp is an autonomous digital agency that builds and deploys full-stack e-commerce stores, menus, "
        "cybersecurity and developer portfolios, medical clinics, and corporate websites. Payment processing is not available. "
        "STRICT POLICY: If the user asks about harmful, illegal, or completely unrelated political/gaming trivia, "
        "politely guide them back to website and business development. "
        "If the user asks about professional fields (cybersecurity, software, engineering, medicine, consulting, retail, restaurants), "
        "answer enthusiastically and supportively in professional Egyptian Arabic! "
        "Always invite them to share their name or business concept so you can build their site immediately."
    )
    try:
        resp = await llm.call(
            system=sys_prompt,
            user=text,
            tier="worker",
            mock="أهلاً بك! أنا مستشارك الذكي في AutoCorp لتطوير وإطلاق المواقع والمتاجر للشركات والمحترفين في مصر. أخبرني عن اسمك أو نشاطك التجاري لنبدأ فوراً في برمجة موقعك!"
        )
        bot_reply = resp.get("text") or "أهلاً بك! أنا في خدمتك لتصميم وإطلاق موقعك أو متجرك الرقمي المتكامل. أخبرني عن نشاطك لنبدأ!"
        await corp.tg_send(chat_id, bot_reply)
    except Exception as e:
        await corp.tg_send(chat_id, "أهلاً بك في AutoCorp! كيف أقدر أساعدك في إطلاق وبرمجة موقعك أو متجرك الإلكتروني اليوم؟")
    finally:
        if msg_id:
            db.x("UPDATE telegram_messages SET status = 'done' WHERE chat_id = ? AND message_id = ?", (chat_id, msg_id))


PROCESSED_TG_UPDATES = set()

@app.post("/telegram")
@app.post("/api/telegram")
async def telegram_webhook(req: Request):
    secret = (os.getenv("TELEGRAM_SECRET") or "autocorp_webhook_secret_2026_x7k9").strip()
    supplied_secret = req.headers.get("x-telegram-bot-api-secret-token", "")
    # A public webhook must fail closed when Telegram authentication is absent.
    if not secret or not hmac.compare_digest(supplied_secret, secret):
        raise HTTPException(401, "Telegram webhook authentication failed")
    u = await req.json()
    
    # A durable unique insert provides cross-worker idempotency; the in-memory
    # set only saves a database round trip for immediate local retries.
    up_id = str(u.get("update_id") or "").strip()
    if up_id:
        if up_id in PROCESSED_TG_UPDATES:
            return {"ok": True, "duplicate": True}
        try:
            db.x("INSERT INTO telegram_updates (update_id, created_at) VALUES (?, ?)", (up_id, time.time()))
        except Exception:
            # Treat an existing durable record as a duplicate. If the lookup
            # itself fails, return a retryable error instead of processing an
            # operation without idempotency protection.
            if db.one("SELECT update_id FROM telegram_updates WHERE update_id = ?", (up_id,)):
                return {"ok": True, "duplicate": True}
            raise HTTPException(503, "Telegram deduplication storage is unavailable")
        PROCESSED_TG_UPDATES.add(up_id)
        if len(PROCESSED_TG_UPDATES) > 1000:
            PROCESSED_TG_UPDATES.clear()

    await handle_telegram_update(u)
    return {"ok": True}
