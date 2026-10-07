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
import json
import os
import random
import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import auth, builder, corp, db, llm, roles, skills, tools

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
    db.init()
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


# =========================================================
# Subdomain Middleware
# =========================================================
@app.middleware("http")
async def subdomain_middleware(request: Request, call_next):
    """Allows accessing sites via subdomain like 3.localhost:8000 or koshary.localhost:8000."""
    host = request.headers.get("host", "").split(":")[0].lower()
    parts = host.split(".")
    # If host has subdomain e.g. 'site-3' or 'koshary'
    if len(parts) >= 2 and parts[0] not in ("www", "api", "admin", "localhost", "127"):
        sub = parts[0]
        if sub.isdigit() and not request.url.path.startswith(f"/sites/{sub}") and not request.url.path.startswith("/api/"):
            request.scope["path"] = f"/sites/{sub}" + request.url.path
        elif not request.url.path.startswith("/api/") and not request.url.path.startswith("/sites/"):
            # Check slug
            row = db.one("select job_id from site_pages where slug=?", (sub,))
            if row:
                jid = row["job_id"]
                request.scope["path"] = f"/sites/{jid}" + request.url.path
    response = await call_next(request)
    return response


# Mount sites directory locally if not Vercel
if not IS_VERCEL:
    os.makedirs(corp.SITES, exist_ok=True)
    app.mount("/sites-static", StaticFiles(directory=corp.SITES, html=True), name="sites-static")


# =========================================================
# =========================================================
# Auth & Security Helpers
# =========================================================
def guard(env_names, key):
    need = next((os.getenv(n) for n in env_names if os.getenv(n)), "")
    if need and key != need:
        raise HTTPException(401, "Unauthorized: bad key")

def admin(key):
    admin_pwd = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
    admin_key = os.getenv("ADMIN_KEY", "autocorp-admin-secret-2026")
    if key in (admin_pwd, admin_key):
        return
    guard(["ADMIN_KEY"], key)

def get_user_from_headers(x_user_token: str = "", x_admin_key: str = "", authorization: str = "") -> Optional[dict]:
    token = x_user_token or x_admin_key
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if token:
        import urllib.parse
        token = urllib.parse.unquote(str(token).strip())
    return auth.decode_token(token)

def require_site_access(jid: int, x_user_token: str = "", x_admin_key: str = "", authorization: str = "") -> dict:
    user = get_user_from_headers(x_user_token, x_admin_key, authorization)
    if not auth.verify_site_ownership(jid, user):
        raise HTTPException(403, "غير مصرح لك بالوصول لإعدادات أو تحميل هذا المتجر. يرجى تسجيل الدخول بحساب مالك المتجر أو المشرف العام.")
    return user or {}


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
def api_register(body: dict):
    uname = (body.get("username") or "").strip()
    pwd = (body.get("password") or "").strip()
    phone = (body.get("phone") or "").strip()
    try:
        user = auth.register_user(uname, pwd, phone)
        return {"ok": True, "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/auth/login")
def api_login(body: dict):
    uname = (body.get("username") or "").strip()
    pwd = (body.get("password") or "").strip()
    try:
        user = auth.login_user(uname, pwd)
        return {"ok": True, "user": user}
    except ValueError as e:
        raise HTTPException(401, str(e))


@app.get("/api/auth/me")
def api_me(
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    user = get_user_from_headers(x_user_token, x_admin_key, authorization)
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
def admin_login(body: dict):
    """Admin login verifying ADMIN_PASSWORD from environment."""
    pwd = (body.get("password") or "").strip()
    correct_pwd = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
    admin_key = os.getenv("ADMIN_KEY", "autocorp-admin-secret-2026")
    if pwd in (correct_pwd, admin_key):
        return {
            "ok": True,
            "token": admin_key,
            "username": os.getenv("ADMIN_NAME", "المدير العام المشرف"),
            "role": "Super Admin & Agency Director"
        }
    raise HTTPException(401, "كلمة مرور المشرف غير صحيحة")


# =========================================================
# Job Creation & Planning
# =========================================================
def make_job(client, request, user_id=None, sync=False):
    check_guardrails(request)
    jid = db.x(
        "insert into jobs(client,request,status,user_id,created_at) values(?,?,?,?,strftime('%s','now'))",
        ((client or "web-client")[:80], request[:4000], "created", user_id)
    )
    if sync or IS_VERCEL:
        return jid
    else:
        corp.spawn(corp.plan_job(jid))
        return jid


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
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    user = get_user_from_headers(x_user_token, x_admin_key, authorization)
    if not user:
        raise HTTPException(401, "يرجى تسجيل الدخول أو إنشاء حساب أولاً قبل إطلاق وبناء المتجر.")
        
    # Check limit of 2 stores for clients
    try:
        auth.check_user_limit(user)
    except ValueError as e:
        raise HTTPException(403, str(e))
    req = (body.get("request") or "").strip()
    brand_name = (body.get("brand_name") or body.get("client") or "").strip()
    category = (body.get("category") or "").strip()
    slogan = (body.get("slogan") or "").strip()
    
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
        
        # AI answers
        ai_answers = body.get("ai_answers") or []
        for ans in ai_answers:
            if ans.get("a"):
                parts.append(f"- {ans.get('label', 'ملاحظة')}: {ans.get('a')}")
        full_req = "\n".join(parts)
        
    if not full_req:
        raise HTTPException(400, "طلب المشروع أو بيانات المتجر مطلوبة")
    check_guardrails(full_req)
    
    sync = body.get("sync", False) or IS_VERCEL
    client_name = brand_name or body.get("client") or user.get("username") or "عميل-AutoCorp"
    jid = make_job(client_name, full_req, user_id=user.get("id"), sync=sync)
    
    # Save site settings
    db.x("""
        INSERT OR REPLACE INTO site_settings (
            job_id, brand_name, category, custom_domain, color_primary, color_secondary,
            logo_url, phone, whatsapp, address, vodafone_cash, instapay, fawry_code,
            cod_enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        jid, brand_name, category, body.get("custom_domain") or "",
        body.get("color_primary") or "", body.get("color_secondary") or "",
        body.get("logo_url") or "", body.get("phone") or "", body.get("whatsapp") or "",
        body.get("address") or "", body.get("vodafone_cash") or "", body.get("instapay") or "",
        body.get("fawry_code") or "", 1 if body.get("cod_enabled", True) else 0,
        time.time()
    ))
    
    # Save manual items if provided
    items = body.get("items") or []
    for it in items:
        if it.get("title"):
            db.x("""
                INSERT INTO site_items (job_id, title, price, category, description, badge, image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                jid, it.get("title"), float(it.get("price") or 0), it.get("category") or "عام",
                it.get("description") or "", it.get("badge") or "", it.get("image_url") or "", time.time()
            ))
            
    if sync:
        try:
            await corp.plan_job(jid)
            job = db.one("select * from jobs where id=?", (jid,))
            if job and job["status"] not in ("awaiting_plan", "rejected", "failed"):
                await corp.run_job(jid)
        except Exception as e:
            print(f"[SYNC JOB ERROR] {e}")
    return {"id": jid, "brand_name": brand_name, "message": "تم إنشاء المشروع وبدأ فريق الـ Agents في التنفيذ"}


@app.post("/api/hooks/job")
async def hook_job(body: dict, x_hook_key: str = Header(default="")):
    guard(["HOOK_KEY", "ADMIN_KEY"], x_hook_key)
    req = (body.get("request") or "").strip()
    if not req:
        raise HTTPException(400, "طلب المشروع مطلوب")
    check_guardrails(req)
    jid = make_job(body.get("client") or "webhook", req, sync=IS_VERCEL)
    if IS_VERCEL:
        try:
            await corp.plan_job(jid)
        except Exception as e:
            print(f"[HOOK JOB ERROR] {e}")
    return {"id": jid}


@app.get("/api/jobs")
def get_jobs(
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    user = get_user_from_headers(x_user_token, x_admin_key, authorization)
    rows = db.q("""
        SELECT j.*, 
               s.brand_name,
               (select count(*) from site_orders where job_id = j.id) as orders_count 
        FROM jobs j 
        LEFT JOIN site_settings s ON s.job_id = j.id
        ORDER BY j.id desc limit 40
    """)
    if not rows:
        return []
        
    jids = [j["id"] for j in rows]
    placeholders = ",".join("?" for _ in jids)
    events_raw = db.q(f"select job_id, msg from events where job_id in ({placeholders}) order by id desc", tuple(jids))
    
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
    return rows


@app.get("/api/jobs/{jid}")
def get_job_detail(
    jid: int,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    user = get_user_from_headers(x_user_token, x_admin_key, authorization)
    j = db.one("select * from jobs where id=?", (jid,))
    if not j:
        raise HTTPException(404, "المشروع غير موجود")
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
async def job_decision(jid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    decision = body.get("decision", "approve")
    return await corp.decide(jid, decision)


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
    """Backend API: Returns site metadata, active routes, and gateway status."""
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
            {"method": "POST", "path": f"/api/sites/{jid}/orders", "desc": "إنشاء طلب جديد ودفع إلكتروني"},
            {"method": "GET", "path": f"/api/sites/{jid}/orders", "desc": "عرض طلبات العملاء"}
        ],
        "stats": {
            "total_orders": orders_c,
            "catalog_items": items_c
        },
        "payment_gateways": {
            "vodafone_cash": os.getenv("VODAFONE_CASH_WALLET", "01023456789"),
            "fawry": os.getenv("FAWRY_MERCHANT_CODE", "10101"),
            "instapay": os.getenv("INSTAPAY_ADDRESS", "sme.egypt@instapay"),
            "paymob_card": bool(os.getenv("PAYMOB_API_KEY")),
            "cash_on_delivery": True
        }
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
async def site_backend_place_order(slug_or_id: str, body: dict):
    """Backend API: Processes real orders and bookings submitted from the generated frontend."""
    jid = resolve_job_id(slug_or_id)
    cust_name = str(body.get("customer_name") or "عميل كريم")[:100]
    cust_phone = str(body.get("customer_phone") or "")[:30]
    cust_addr = str(body.get("customer_address") or "استلام من الفرع")[:200]
    items = body.get("items") or []
    total_egp = float(body.get("total_egp") or 0.0)
    pay_method = str(body.get("payment_method") or "cash")[:30]
    
    if pay_method.lower() in ("fawry", "fawry_pay"):
        ref_code = f"FAWRY-{random.randint(10000000, 99999999)}"
        pay_note = f"ادفع برقم فوري {ref_code} خلال 48 ساعة"
    elif "vodafone" in pay_method.lower() or "wallet" in pay_method.lower():
        ref_code = f"VF-{random.randint(100000, 999999)}"
        pay_note = f"تم التحويل لمحفظة {os.getenv('VODAFONE_CASH_WALLET', '01023456789')}"
    elif "instapay" in pay_method.lower():
        ref_code = f"IP-{random.randint(100000, 999999)}"
        pay_note = f"تحويل إنستاباي إلى {os.getenv('INSTAPAY_ADDRESS', 'sme.egypt@instapay')}"
    else:
        ref_code = f"COD-{random.randint(1000, 9999)}"
        pay_note = "الدفع نقداً عند استلام الأوردر"

    order_id = db.x(
        "insert into site_orders(job_id, customer_name, customer_phone, customer_address, items_json, total_egp, payment_method, payment_ref, status, created_at) values(?,?,?,?,?,?,?,?,?,?)",
        (jid, cust_name, cust_phone, cust_addr, json.dumps(items, ensure_ascii=False), total_egp, pay_method, ref_code, "confirmed", time.time())
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
        "status": "confirmed",
        "message": "تم استلام وتأكيد طلبك بنجاح وجاري تجهيزه للتسليم!"
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
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    db.x("""
        INSERT OR REPLACE INTO site_settings (
            job_id, brand_name, category, custom_domain, color_primary, color_secondary,
            logo_url, phone, whatsapp, address, vodafone_cash, instapay, fawry_code,
            cod_enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        jid, body.get("brand_name"), body.get("category"), body.get("custom_domain"),
        body.get("color_primary"), body.get("color_secondary"), body.get("logo_url"),
        body.get("phone"), body.get("whatsapp"), body.get("address"), body.get("vodafone_cash"),
        body.get("instapay"), body.get("fawry_code"), 1 if body.get("cod_enabled", True) else 0,
        time.time()
    ))
    job_row = db.one("select * from jobs where id=?", (jid,)) or {}
    items_rows = db.q("select * from site_items where job_id=?", (jid,))
    new_html = builder.build_site_html(jid, job_row.get("client") or "", job_row.get("request") or "", settings=body, items=items_rows)
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
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=autocorp_enterprise_site_{jid}.zip"}
    )


@app.post("/api/sites/{slug_or_id}/deploy-github")
async def deploy_site_github(
    slug_or_id: str,
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Directly pushes full project repository to the user's personal GitHub account."""
    import base64
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    
    token = (body.get("github_token") or "").strip()
    if not token:
        raise HTTPException(400, "يرجى إدخال رمز الوصول الشخصي (GitHub Personal Access Token)")
        
    repo_name = (body.get("repo_name") or f"autocorp-site-{jid}").strip()
    repo_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', repo_name).strip('-')
    is_private = bool(body.get("is_private", False))

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
    body: dict,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    """Deploys the site directly to Vercel using Deploy Hook or Vercel Token."""
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    
    deploy_hook = (body.get("deploy_hook") or "").strip()
    vercel_token = (body.get("vercel_token") or "").strip()
    project_name = (body.get("project_name") or f"autocorp-site-{jid}").strip().lower()
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
    deployment_id: str,
    vercel_token: str,
    x_user_token: str = Header(default=""),
    x_admin_key: str = Header(default=""),
    authorization: str = Header(default="")
):
    jid = resolve_job_id(slug_or_id)
    require_site_access(jid, x_user_token, x_admin_key, authorization)
    
    headers = {"Authorization": f"Bearer {vercel_token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"https://api.vercel.com/v13/deployments/{deployment_id}", headers=headers)
        if r.status_code == 200:
            d = r.json()
            return {
                "ok": True,
                "status": d.get("readyState"),
                "url": "https://" + d.get("url") if d.get("url") else None,
                "error": d.get("error")
            }
        return {"ok": False, "status": "UNKNOWN"}


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

@app.get("/api/posts")
def get_posts():
    return db.q("select * from posts order by id desc limit 15")

@app.post("/api/posts/{pid}/decision")
async def post_decision(pid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    decision = body.get("decision", "approve")
    return await corp.decide_post(pid, decision)

@app.get("/api/proposals")
def get_proposals():
    return db.q("select id,kind,target,reason,status,substr(content,1,600) content from proposals order by id desc limit 15")

@app.post("/api/proposals/{pid}/decision")
async def proposal_decision(pid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    d = body.get("decision", "approve")
    return await (corp.rollback_proposal(pid) if d == "rollback" else corp.decide_proposal(pid, d))


# =========================================================
# Company Introspection & Financial Summary
# =========================================================
@app.get("/api/summary")
def get_summary():
    row = db.one("""
        select 
            coalesce((select sum(delta) from ledger where account='client_payment'), 0) as rev,
            coalesce((select sum(delta) from ledger where account like 'payroll:%'), 0) as pay,
            (select count(*) from site_orders) as total_orders,
            (select count(*) from site_pages) as total_sites,
            (select count(*) from agents) as hired_agents,
            (select count(*) from jobs) as total_jobs
    """) or {}
    
    rev_v = float(row.get("rev", 0) or 0)
    pay_v = -float(row.get("pay", 0) or 0)
    
    return {
        "revenue_egp": round(rev_v, 2),
        "payroll_egp": round(pay_v, 3),
        "profit_egp": round(rev_v - pay_v, 2),
        "margin_percent": round(((rev_v - pay_v) / rev_v * 100), 1) if rev_v > 0 else 0,
        "hired_agents": int(row.get("hired_agents", 0) or 0),
        "roster_roles": len(roles.all_names()),
        "jobs": int(row.get("total_jobs", 0) or 0),
        "generated_sites": int(row.get("total_sites", 0) or 0),
        "total_store_orders": int(row.get("total_orders", 0) or 0)
    }


@app.get("/api/ledger")
def get_ledger(x_admin_key: str = Header(default="")):
    return db.q("select id, ts, account, delta, memo, job_id from ledger order by id desc limit 40")


@app.get("/api/agents")
def get_agents():
    return db.q("select name,department,origin,uses,round(balance,3) balance from agents order by uses desc, name")


@app.get("/api/roster")
def get_roster():
    return {"total": len(roles.all_names()), "departments": {d: list(r) for d, r in roles.DEPARTMENTS.items()}}


@app.get("/api/providers")
def get_providers():
    return llm.status()


@app.post("/api/providers/test")
async def test_providers(x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    return await llm.test_all()


@app.api_route("/api/tick", methods=["GET", "POST"])
async def trigger_tick(x_cron_key: str = Header(default=""), key: str = ""):
    guard(["CRON_KEY", "ADMIN_KEY"], x_cron_key or key)
    return await corp.tick()


def extract_smart_brand(prompt: str, niche: str) -> str:
    p = prompt.strip()
    
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
                    return f"{extracted} | خبير الأمن السيبراني"
                return extracted

    # 2. Portfolio personal names heuristics
    if niche in ("portfolio", "cybersecurity") or any(k in p for k in ["سايبر", "سيكيورتي", "بورتفوليو", "بروفايل", "مبرمج"]):
        name_m = re.search(r'\b(ياسين|أحمد|احمد|محمد|محمود|علي|عمر|خالد|إبراهيم|ابراهيم|فاروق|كريم|طارق|يوسف|سارة|نور)\s+([^\n،,\.؛\s]+)', p)
        if name_m:
            return f"{name_m.group(0)} | خبير الأمن السيبراني"
        return "بورتفوليو مهندس الأمن السيبراني"

    # 3. Specialty Honey
    if niche == "honey" or any(k in p for k in ["عسل", "نحل", "سدر", "مناحل"]):
        return "مناحل الشفاء | متجر العسل الطبيعي الأصلي"

    # 4. Standard business niches
    if any(k in p for k in ["اجهز", "الكترون", "موبايل", "هواتف", "سماعات", "شواحن", "لابتوب"]):
        return "تكنو زون للأجهزة والإلكترونيات"
    if "كبابجي" in p or "مشويات" in p or "حواوشي" in p:
        return "مطعم ومشويات كبابجي الأصيل"
    if "خضار" in p or "فاكه" in p or "فواكه" in p:
        return "سوق الخضار والفواكه الطازجة"
    if "سوبرماركت" in p or "بقالة" in p or "ماركت" in p:
        return "سوبرماركت البركة ماركت"
    if "كافيه" in p or "قهوة" in p or "مقهى" in p or "بن" in p:
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
    admin_pwd = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
    
    cb = u.get("callback_query")
    if cb:
        cb_id = cb["id"]
        from_id = str(cb["from"]["id"])
        data = cb.get("data", "")
        
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
    
    # Message Deduplication: Prevent handling duplicate Telegram deliveries
    if msg_id:
        try:
            seen_msg = db.one("SELECT status FROM telegram_messages WHERE chat_id = ? AND message_id = ?", (chat_id, msg_id))
            if seen_msg:
                print(f"[TG DEDUP] Message #{msg_id} in chat {chat_id} already processed. Skipping duplicate.")
                return
            db.x("INSERT OR REPLACE INTO telegram_messages (chat_id, message_id, status, created_at) VALUES (?, ?, 'processing', ?)", (chat_id, msg_id, time.time()))
        except Exception as e:
            print(f"[TG MSG DEDUP ERR] {e}")

    # Check if this telegram user is linked to an account
    linked_user = db.one("SELECT id, username, role FROM users WHERE telegram_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    user_id = linked_user["id"] if linked_user else None
    user_name = linked_user["username"] if linked_user else f"tg:{chat_id}"
    is_user_admin = (linked_user and linked_user.get("role") == "admin") or (os.getenv("TELEGRAM_OWNER_CHAT_ID") == chat_id) or (user_name.lower() in ("admin", "alfarouq", "alfarouqibrahim", "alfarouq123"))

    # 1. /start command
    if text.startswith("/start"):
        await corp.tg_send(
            chat_id,
            "مرحباً بك في AutoCorp 🤖🇪🇬\n"
            "وكالة الذكاء الاصطناعي ذاتية التشغيل للمتاجر والشركات والمحترفين في مصر.\n\n"
            "✨ يسعدني التحدث معك ومساعدتك في إطلاق موقع متكامل بالفرونت والباك إند وبوابات الدفع المصرية في أقل من دقيقة!\n\n"
            "📋 الأوامر المتاحة:\n"
            "• /register <اسم_المستخدم> <كلمة_المرور> — إنشاء حساب جديد\n"
            "• /login <اسم_المستخدم> <كلمة_المرور> — تسجيل الدخول\n"
            "• /my_sites — عرض مواقعك ومتاجرك المنشورة وروابطها\n"
            "• /build <وصف الموقع أو المتجر> — إطلاق وبرمجة موقعك فوراً\n"
            "• /help — دليل استخدام الوكالة والخدمات المتاحة\n"
            "• /admin <كلمة_المرور> — تسجيل دخول المدير المشرف\n\n"
            "💡 أو ببساطة: اكتب فكرة موقعك (مثال: 'عايز اعمل بورتفوليو لواحد اسمه ياسين احمد في السايبر سيكيورتي' أو 'متجر بيع عسل') وسأنفذه فوراً!"
        )
        return

    # 2. /help command
    if text.startswith("/help"):
        await corp.tg_send(
            chat_id,
            "📖 دليل استخدام مستشار AutoCorp الذكي:\n\n"
            "1️⃣ بناء المواقع والمتاجر: اكتب تفاصيل نشاطك (مثال: 'بورتفوليو أمن سيبراني لـ ياسين أحمد' أو 'متجر عسل سدر فاخر' أو 'مطعم مشويات') أو أرسل صورة المنيو/البضاعة.\n"
            "2️⃣ بوابات الدفع والحجز: كل موقع يتم تجهيزه تلقائياً بروابط فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام أو فواتير التعاقد.\n"
            "3️⃣ باقة البداية المجانية: تتيح لك تجربة بناء حتى (موقعين) مجاناً.\n"
            "4️⃣ استضافة هوستينجر وGitHub: يمكنك تحميل كود الإنتاج كاملاً بملف ZIP أو النشر المباشر على GitHub و Vercel.\n\n"
            "لربط حسابك: اكتب /login اسم_المستخدم كلمة_المرور"
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
            if u_name.lower() in ("admin", "alfarouq", "alfarouqibrahim", "alfarouq123") or u_pass == os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim"):
                os.environ["TELEGRAM_OWNER_CHAT_ID"] = chat_id
                db.x("UPDATE users SET role = 'admin' WHERE id = ?", (res["id"],))
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
            if res.get("is_admin") or u_name.lower() in ("admin", "alfarouq", "alfarouqibrahim", "alfarouq123") or u_pass == os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim"):
                os.environ["TELEGRAM_OWNER_CHAT_ID"] = chat_id
                if res.get("id"):
                    db.x("UPDATE users SET role = 'admin' WHERE id = ?", (res["id"],))
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
        msg_lines.append("\n💡 يمكنك تحميل حزمة هوستينجر أو ربط دومين خاص بك من لوحة تحكم الويب.")
        await corp.tg_send(chat_id, "\n".join(msg_lines))
        return

    # 6. /admin login command
    if text.startswith("/admin"):
        parts = text.split(maxsplit=1)
        admin_pwd = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
        if len(parts) > 1 and parts[1].strip() == admin_pwd:
            os.environ["TELEGRAM_OWNER_CHAT_ID"] = chat_id
            admin_name = os.getenv("ADMIN_NAME", "Alfarouq Ibrahim")
            await corp.tg_send(
                chat_id,
                f"👑 أهلاً بك ({admin_name})! تم تسجيلك كمدير مشرف على AutoCorp بنجاح.\n"
                "ستصلك قرارات التسعير واعتمادات التسليم هنا لتوافق عليها بضغطة زر."
            )
        else:
            await corp.tg_send(chat_id, "❌ كلمة المرور غير صحيحة.")
        return

    # 7. Conversational Handling & Guardrails
    check_guardrails(text)
    
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
        if any(t_clean == g or t_clean.startswith(g + " ") for g in greetings) and len(t_clean) < 35 and not msg.get("photo"):
            await corp.tg_send(
                chat_id,
                "أهلاً بك يا فندم! 🤖🇪🇬\n"
                "أنا المستشار الذكي لوكالة AutoCorp لبناء وتطوير المواقع والمتاجر للشركات والمحترفين في مصر.\n\n"
                "مهمتي أساعدك في إطلاق موقع أو متجر إلكتروني متكامل لنشاطك التجاري أو بورتفوليو شخصي في أقل من دقيقة، "
                "مع بوابات الدفع المصرية (فودافون كاش، إنستاباي، فوري) وتصميم متجاوب بالكامل.\n\n"
                "💡 كيف تحب نبدأ؟\n"
                "• لبدء البناء فوراً: اكتب تفاصيل نشاطك (مثال: 'عايز اعمل بورتفوليو لواحد اسمه ياسين احمد في السايبر سيكيورتي' أو 'متجر عسل').\n"
                "• لتسجيل الدخول: اكتب /login اسم_المستخدم كلمة_المرور\n"
                "• أو اسألني أي سؤال حول الميزات والأسعار وبوابات الدفع!"
            )
            return
        is_store_request = bool(msg.get("photo")) or is_store_creation_intent(text)

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
                    "يمكنك استعراض مواقعك السابقة عبر كتابة /my_sites أو الترقية لإنشاء مواقع جديدة."
                )
                return

        if msg.get("photo"):
            desc = await corp.tg_image_to_text(msg["photo"][-1]["file_id"], text)
            text = f"{text}\n\n[تحليل صورة العميل بواسطة Vision Analyst]:\n{desc}".strip()
            
        niche = builder.detect_niche(text)
        brand = extract_smart_brand(text, niche)

        # Check if user only specified a person's name without any niche or activity
        has_niche_clue = any(k in text.lower() for k in [
            "سايبر", "سيكيورتي", "أمن", "امن", "برمج", "مطور", "عسل", "مطعم", "خضار", "اجهز",
            "ملابس", "عياد", "دكتور", "شركة", "وكالة", "بورتفوليو", "متجر", "محل", "كافيه"
        ])
        if not has_niche_clue and any(k in text for k in ["لواحد اسمه", "واحد اسمه", "اسمه"]) and len(text.split()) <= 6:
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

        pal_key = "cyber" if niche == "portfolio" else "amber" if niche == "honey" else "sunset" if niche == "restaurant" else "emerald" if niche == "vegetables" else "teal" if niche == "clinic" else "indigo" if niche == "agency" else "ocean"
        pal = builder.PALETTES.get(pal_key, builder.PALETTES["emerald"])
        
        # Prevent rapid duplicates
        recent = db.one(
            "SELECT id FROM jobs WHERE client = ? AND request = ? AND created_at > ?",
            (brand, text, time.time() - 60)
        )
        if recent:
            print(f"[TG DEDUP] Skipping duplicate creation for {brand} (Job #{recent['id']})")
            return

        # Create job in DB with delivered status
        jid = db.x(
            "INSERT INTO jobs(client, request, status, user_id, price, cost, created_at) VALUES(?, ?, 'delivered', ?, 299.0, 0.0, ?)",
            (brand[:80], text[:4000], user_id, time.time())
        )
        
        # Save initial settings
        settings = {
            "brand_name": brand,
            "category": niche,
            "color_primary": pal["primary"],
            "color_secondary": pal["secondary"],
            "phone": "01000000000",
            "whatsapp": "01000000000",
            "vodafone_cash": "01000000000",
            "instapay": f"{arabic_to_english_slug(brand)[:15]}@instapay",
            "fawry_code": "88219",
            "cod_enabled": 1
        }
        db.x("""
            INSERT OR REPLACE INTO site_settings (
                job_id, brand_name, category, color_primary, color_secondary,
                phone, whatsapp, vodafone_cash, instapay, fawry_code, cod_enabled, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            jid, brand, niche, pal["primary"], pal["secondary"],
            settings["phone"], settings["whatsapp"], settings["vodafone_cash"], settings["instapay"],
            settings["fawry_code"], 1, time.time()
        ))
        
        # Insert default catalog items
        default_items = builder.DEFAULT_CATALOGS.get(niche, builder.DEFAULT_CATALOGS["general"])
        for it in default_items:
            db.x("INSERT INTO site_items(job_id, title, price, category, description, badge, created_at) VALUES(?,?,?,?,?,?,?)",
                 (jid, it["title"], it["price"], it["category"], it["desc"], it.get("badge", ""), time.time()))
                 
        db_items = db.q("SELECT * FROM site_items WHERE job_id = ? ORDER BY id", (jid,))
        
        # Synthesize HTML immediately (< 5ms execution!)
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

        if niche == "portfolio":
            congrats_msg = (
                f"🎉 تم إطلاق وبرمجة موقعك الشخصي (Portfolio) بنجاح وهو الآن شغال 100%! 🚀\n\n"
                f"👤 الاسم والمهنة: {brand}\n"
                f"🛡️ التخصص: أمن سيبراني واختبار اختراق متقدم\n"
                f"🎨 الهوية: ثيم تقني داكن عالي الاحترافية (Cyber Dark Mode)\n"
                f"💼 المميزات: معرض أعمال، مصفوفة مهارات وشهادات معتمدة، ونظام حجز واستشارة فوري!\n\n"
                f"🌐 رابط موقعك المباشر:\n{site_link}\n\n"
                f"💡 يمكنك فتح الرابط ومشاركته فوراً، أو تحميل حزمة هوستينجر / ربط دومين خاص من لوحة تحكم الويب."
            )
        else:
            congrats_msg = (
                f"🎉 تم إطلاق وبرمجة متجرك الإلكتروني بنجاح وهو الآن شغال 100%! 🚀\n\n"
                f"🏷️ اسم المتجر: {brand}\n"
                f"🛒 نوع النشاط: {niche}\n"
                f"🎨 الهوية: تم تفعيل باليت ألوان عصرية متناسقة ({pal_key})\n"
                f"💳 بوابات الدفع المفعلة: فودافون كاش، إنستاباي، فوري، والدفع عند الاستلام\n\n"
                f"🌐 رابط متجرك المباشر:\n{site_link}\n\n"
                f"💡 يمكنك فتح المتجر، تجربة إضافة المنتجات للسلة، أو تسجيل الدخول على لوحة التحكم وإدارته بحسابك ({user_name})!"
            )
            
        await corp.tg_send(chat_id, congrats_msg)
        if msg_id:
            db.x("UPDATE telegram_messages SET status = 'done' WHERE chat_id = ? AND message_id = ?", (chat_id, msg_id))
        return

    # 7.3 General Consultation Chat with Scope Guardrail
    sys_prompt = (
        "You are AutoCorp's friendly, highly knowledgeable Egyptian AI consultant for businesses, professionals, and freelancers. "
        "AutoCorp is an autonomous digital agency that builds and deploys full-stack e-commerce stores, menus, "
        "cybersecurity and developer portfolios, medical clinics, and corporate websites with Egyptian payment gateways in seconds. "
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
async def telegram_webhook(req: Request):
    secret = os.getenv("TELEGRAM_SECRET")
    if secret and req.headers.get("x-telegram-bot-api-secret-token") != secret:
        raise HTTPException(401)
    u = await req.json()
    
    # Deduplication by update_id in-memory and in Turso Cloud
    up_id = str(u.get("update_id") or "").strip()
    if up_id:
        if up_id in PROCESSED_TG_UPDATES:
            return {"ok": True, "duplicate": True}
        PROCESSED_TG_UPDATES.add(up_id)
        if len(PROCESSED_TG_UPDATES) > 1000:
            PROCESSED_TG_UPDATES.clear()
            
        try:
            existing = db.one("SELECT update_id FROM telegram_updates WHERE update_id = ?", (up_id,))
            if existing:
                return {"ok": True, "duplicate": True}
            db.x("INSERT OR REPLACE INTO telegram_updates (update_id, created_at) VALUES (?, ?)", (up_id, time.time()))
        except Exception as e:
            print(f"[TG DEDUP DB ERR] {e}")

    await handle_telegram_update(u)
    return {"ok": True}
