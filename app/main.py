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


def make_site_slug(jid: int, brand: str = "") -> str:
    clean = re.sub(r'[\s_]+', '-', str(brand or "").strip())
    clean = re.sub(r'[^\w\u0600-\u06FF\-]+', '', clean)
    clean = clean.strip('-')
    if clean:
        return f"{jid}-{clean}"
    return str(jid)


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
    
    creation_verbs = ["انشا", "تنشا", "اعمل", "تعمل", "صمم", "ابني", "تبني", "بناء", "برمج", "تطوير", "اطلق", "سوي", "كريت", "build", "create", "make"]
    target_nouns = ["موقع", "ويب", "متجر", "ستور", "صفحه", "منيو", "مشروع"]
    desire_words = ["عايز", "عاوز", "اريد", "حابب", "ودي", "محتاج", "لازم", "نفسي"]
    
    has_verb = any(v in t for v in creation_verbs)
    has_noun = any(n in t for n in target_nouns)
    has_desire = any(d in t for d in desire_words)
    
    if has_verb and has_noun:
        return True
    if has_desire and has_noun:
        return True
    if has_desire and any(k in t for k in ["بيع", "محل", "مطعم", "كافيه", "سوبرماركت", "صيدليه", "خضار", "اجهز", "الكترون"]):
        return True
    if any(k in t for k in ["/build", "ابدأ البناء", "انشاء متجر", "عمل موقع", "بناء متجر"]):
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
    
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", row["html"])
        zf.writestr("api_config.json", json.dumps({
            "site_id": jid,
            "brand_name": brand,
            "backend_url": f"http://localhost:8000/api/sites/{jid}",
            "payment_support": ["vodafone_cash", "instapay", "fawry", "cod"],
            "generated_by": "AutoCorp AI Autonomous Agency"
        }, ensure_ascii=False, indent=2))
        readme_txt = (
            "===========================================================\n"
            "⚡ AutoCorp — تعليمات رفع الموقع على استضافة هوستينجر (Hostinger)\n"
            "===========================================================\n"
            f"المشروع: {brand} (المعرف: #{jid})\n"
            "التاريخ: 2026\n\n"
            "خطوات الرفع السريع (في أقل من دقيقة):\n"
            "1. افتح لوحة تحكم هوستينجر (hPanel).\n"
            "2. ادخل إلى 'إدارة الملفات' (File Manager) للموقع الخاص بك.\n"
            "3. افتح المجلد الرئيسي: public_html\n"
            "4. قم برفع هذا الملف المضغوط وفك الضغط عنه (Extract).\n"
            "5. تأكد من وجود ملف index.html مباشرة داخل مجلد public_html.\n"
            "6. موقعك أصبح الآن شغال 100% ومربوط ببوابات الدفع والسلة!\n\n"
            "لربط دومين مخصص (Custom Domain):\n"
            "- اذهب إلى إعدادات DNS في هوستينجر أو Cloudflare.\n"
            "- أضف سجل CNAME يشير إلى: cname.autocorp.io (أو عنوان السيرفر).\n"
            "===========================================================\n"
        )
        zf.writestr("README_DEPLOY_HOSTINGER.txt", readme_txt)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=autocorp_site_{jid}.zip"}
    )


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
    if "حلويات" in p or "تورتة" in p or "بسبوسة" in p or "شوكولاتة" in p:
        return "حلواني قصر السعادة"
    if "سمك" in p or "اسماك" in p or "بحريات" in p or "جمبري" in p:
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
    text = (msg.get("text") or msg.get("caption") or "").strip()
    
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
            "وكالة الذكاء الاصطناعي ذاتية التشغيل للمتاجر والشركات المصرية.\n\n"
            "✨ يسعدني التحدث معك ومساعدتك في إطلاق موقع متكامل بالفرونت والباك إند وبوابات الدفع المصرية في أقل من دقيقتين!\n\n"
            "📋 الأوامر المتاحة:\n"
            "• /register <اسم_المستخدم> <كلمة_المرور> — إنشاء حساب جديد\n"
            "• /login <اسم_المستخدم> <كلمة_المرور> — تسجيل الدخول\n"
            "• /my_sites — عرض متاجرك الإلكترونية وروابطها\n"
            "• /build <وصف المتجر> — إطلاق وبرمجة متجر فوراً\n"
            "• /help — دليل استخدام الوكالة والخدمات المتاحة\n"
            "• /admin <كلمة_المرور> — تسجيل دخول المدير المشرف\n\n"
            "💡 أو ببساطة: تحدث معي واشرح لي فكرة متجرك وسأقوم بإرشادك خطوة بخطوة!"
        )
        return

    # 2. /help command
    if text.startswith("/help"):
        await corp.tg_send(
            chat_id,
            "📖 دليل استخدام مستشار AutoCorp الذكي:\n\n"
            "1️⃣ بناء المتاجر: فقط اكتب تفاصيل متجرك (مثال: 'عايز متجر خضار وفواكه فريش' أو 'مطعم مشويات') أو أرسل صورة المنيو/البضاعة.\n"
            "2️⃣ بوابات الدفع: كل متجر يتم تجهيزه تلقائياً بروابط فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام.\n"
            "3️⃣ باقة البداية المجانية: تتيح لك تجربة بناء حتى (موقعين) مجاناً.\n"
            "4️⃣ استضافة هوستينجر: يمكنك تحميل كود الإنتاج كاملاً بملف ZIP من لوحة التحكم ورفعه على استضافتك بضغطة زر.\n\n"
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
                f"تم تفعيل باقة البداية (رصيد حتى موقعين مجاناً). يمكنك الآن طلب متجرك الأول!"
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
                "أنت الآن جاهز لإدارة متاجرك أو طلب بناء متجر جديد."
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
            await corp.tg_send(chat_id, "🛒 ليس لديك أي متاجر منشورة حتى الآن. لإنشاء متجرك الأول، اكتب وصف نشاطك التجاري أو استخدم /build.")
            return
        base_url = "https://autocorp-ai-websits-builder.vercel.app" if IS_VERCEL else "http://localhost:8000"
        msg_lines = ["📱 متاجرك الإلكترونية في AutoCorp:\n"]
        for s in sites:
            paid_str = "✅ نشط ومدفوع" if s.get("is_paid") else "⏳ تجريبي / في انتظار التفعيل"
            slug = make_site_slug(s['id'], s['client'])
            msg_lines.append(
                f"• متجر #{s['id']} ({s['client']})\n"
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
    
    # 7.1 Greeting Detection
    greetings = ["اهلا", "أهلا", "مرحبا", "سلام", "السلام عليكم", "ازيك", "صباح الخير", "مساء الخير", "هاي", "الو", "مين انت", "عرفني بيك"]
    t_clean = text.lower().strip()
    if any(t_clean == g or t_clean.startswith(g + " ") for g in greetings) and len(t_clean) < 35 and not msg.get("photo"):
        await corp.tg_send(
            chat_id,
            "أهلاً بك يا فندم! 🤖🇪🇬\n"
            "أنا المستشار الذكي لوكالة AutoCorp لبناء وتطوير المواقع والمتاجر للشركات المصرية.\n\n"
            "مهمتي أساعدك في إطلاق متجر إلكتروني وتطبيق ويب متكامل لنشاطك التجاري في أقل من دقيقتين، "
            "مع سلة مشتريات وبوابات الدفع المصرية (فودافون كاش، إنستاباي، فوري) وتصميم متجاوب بالكامل.\n\n"
            "💡 كيف تحب نبدأ؟\n"
            "• لبدء بناء متجرك فوراً: اكتب تفاصيل نشاطك (مثال: 'عايز اعمل متجر لبيع الخضار والفواكه' أو 'مطعم مشويات').\n"
            "• لتسجيل الدخول: اكتب /login اسم_المستخدم كلمة_المرور\n"
            "• أو اسألني أي سؤال حول الميزات والأسعار وبوابات الدفع!"
        )
        return

    # 7.2 Store Creation Intent Detection
    is_store_request = bool(msg.get("photo")) or is_store_creation_intent(text)

    if is_store_request:
        # Check 2-store limit for non-admin users
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
                    "يمكنك استعراض متاجرك السابقة عبر كتابة /my_sites أو الترقية لإنشاء مواقع جديدة."
                )
                return

        if msg.get("photo"):
            desc = await corp.tg_image_to_text(msg["photo"][-1]["file_id"], text)
            text = f"{text}\n\n[تحليل صورة العميل بواسطة Vision Analyst]:\n{desc}".strip()
            
        niche = builder.detect_niche(text)
        brand = extract_smart_brand(text, niche)
        pal_key = "emerald" if niche == "vegetables" else "sunset" if niche == "restaurant" else "ocean"
        pal = builder.PALETTES.get(pal_key, builder.PALETTES["emerald"])
        
        # Prevent duplicate job creation from Telegram webhook retries
        recent = db.one(
            "SELECT id FROM jobs WHERE client = ? AND request = ? AND created_at > ?",
            (brand, text, time.time() - 120)
        )
        if recent:
            print(f"[TG DEDUP] Skipping duplicate creation for {brand} (Job #{recent['id']})")
            return

        # Always set client as the actual brand name
        jid = make_job(brand, text, user_id=user_id, sync=True)
        
        # Save initial site settings
        db.x("""
            INSERT OR REPLACE INTO site_settings (
                job_id, brand_name, category, color_primary, color_secondary,
                phone, whatsapp, vodafone_cash, instapay, fawry_code, cod_enabled, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            jid, brand, niche, pal["primary"], pal["secondary"],
            "01000000000", "01000000000", "01000000000", f"{brand.replace(' ','').lower()}@instapay",
            "88219", 1, time.time()
        ))
        
        base_url = "https://autocorp-ai-websits-builder.vercel.app" if IS_VERCEL else "http://localhost:8000"
        slug = make_site_slug(jid, brand)
        site_link = f"{base_url}/sites/{slug}/"

        await corp.tg_send(
            chat_id,
            f"🚀 استلمنا طلبك بنجاح! بدأنا الآن العمل على مشروع #{jid} ({brand})...\n\n"
            f"👥 فريق الـ 70 Agent (CEO، مهندس المعمارية، كاتب المحتوى، مطور الواجهات، ومراجع الجودة) يقوم الآن ببناء وبرمجة المتجر بالكامل.\n"
            f"⏳ انتظر ثوانٍ معدودة وسيصلك الرابط المباشر..."
        )
        
        try:
            await corp.plan_job(jid)
            await corp.run_job(jid)
        except Exception as e:
            print(f"[TG JOB EXEC ERR] {e}")

        await corp.tg_send(
            chat_id,
            f"🎉 تم إطلاق وبرمجة متجرك الإلكتروني بنجاح وهو الآن شغال 100%!\n\n"
            f"🏷️ اسم المتجر: {brand}\n"
            f"🛒 نوع النشاط: {niche}\n"
            f"🎨 الهوية: تم تفعيل باليت ألوان عصرية ({pal_key})\n"
            f"💳 بوابات الدفع المفعلة: فودافون كاش، إنستاباي، فوري، والدفع عند الاستلام\n\n"
            f"🌐 رابط متجرك المباشر:\n{site_link}\n\n"
            f"💡 يمكنك فتح المتجر من الرابط، تجربة إضافة المنتجات للسلة، أو تسجيل الدخول على لوحة التحكم وإدارته بحسابك ({user_name})!"
        )
        return

    # 7.3 General Consultation Chat with Scope Guardrail
    sys_prompt = (
        "You are AutoCorp's friendly, professional Egyptian AI consultant for SMEs. "
        "AutoCorp is an autonomous digital agency that builds and deploys full-stack e-commerce stores, "
        "menus, and web apps with Egyptian payment gateways in under 2 minutes. "
        "STRICT POLICY: If the user asks about unrelated topics (politics, school homework, gaming, religion, gossip, general trivia), "
        "you MUST politely refuse and clarify that you only assist with building, designing, and launching digital business stores and websites. "
        "If the user is asking about services, pricing, business categories, or web advice, answer supportively in Egyptian Arabic. "
        "Always end by inviting them to tell you about their business so you can generate their store."
    )
    try:
        resp = await llm.call(
            system=sys_prompt,
            user=text,
            tier="worker",
            mock="أهلاً بك! أنا مستشارك الذكي في AutoCorp لتطوير وإطلاق المواقع والمتاجر للشركات المصرية. أخبرني عن نشاطك التجاري لنبدأ فوراً في برمجة متجرك!"
        )
        bot_reply = resp.get("text") or "أهلاً بك! أنا في خدمتك لتصميم وإطلاق متجرك الرقمي المتكامل. أخبرني عن نشاطك لنبدأ!"
        await corp.tg_send(chat_id, bot_reply)
    except Exception as e:
        await corp.tg_send(chat_id, "أهلاً بك في AutoCorp! كيف أقدر أساعدك في إطلاق وبرمجة متجرك الإلكتروني اليوم؟")


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
