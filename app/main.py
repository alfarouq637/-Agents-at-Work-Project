"""FastAPI application: API routes, Telegram bot polling & webhook, static serving.

Features:
- Subdomain Routing for generated sites (e.g., site-1.localhost or slug.localhost)
- Full-Stack Site Backend APIs (/api/sites/{id}/info, /items, /orders, /checkout)
- Admin Login & Supervision Panel with password AlfarouqIbrahim
- Prompt Injection & Financial Safety Guardrails
- Telegram Bot (@autocorp_Alfarouq_Ibrahim_bot) with auto-polling & approvals
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

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import corp, db, llm, roles, skills, tools

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


# =========================================================
# Admin Authentication API
# =========================================================
@app.post("/api/admin/login")
def admin_login(body: dict):
    """Admin login with password AlfarouqIbrahim."""
    pwd = (body.get("password") or "").strip()
    correct_pwd = os.getenv("ADMIN_PASSWORD", "AlfarouqIbrahim")
    admin_key = os.getenv("ADMIN_KEY", "autocorp-admin-secret-2026")
    if pwd in (correct_pwd, admin_key):
        return {
            "ok": True,
            "token": admin_key,
            "username": "الفاروق إبراهيم (المدير العام المشرف)",
            "role": "Super Admin & Agency Director"
        }
    raise HTTPException(401, "كلمة مرور الأدمن غير صحيحة")


# =========================================================
# Job Creation & Planning
# =========================================================
def make_job(client, request, sync=False):
    check_guardrails(request)
    jid = db.x(
        "insert into jobs(client,request,status,created_at) values(?,?,?,strftime('%s','now'))",
        ((client or "web-client")[:80], request[:4000], "created")
    )
    if sync or IS_VERCEL:
        return jid
    else:
        corp.spawn(corp.plan_job(jid))
        return jid


@app.get("/")
def home():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


@app.post("/api/jobs")
async def new_job(body: dict, x_admin_key: str = Header(default="")):
    req = (body.get("request") or "").strip()
    if not req:
        raise HTTPException(400, "طلب المشروع مطلوب")
    check_guardrails(req)
    
    sync = body.get("sync", False) or IS_VERCEL
    jid = make_job(body.get("client"), req, sync=sync)
    
    if sync:
        try:
            await corp.plan_job(jid)
            job = db.one("select * from jobs where id=?", (jid,))
            if job and job["status"] not in ("awaiting_plan", "rejected", "failed"):
                await corp.run_job(jid)
        except Exception as e:
            print(f"[SYNC JOB ERROR] {e}")
    return {"id": jid}


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
def get_jobs():
    rows = db.q("select * from jobs order by id desc limit 25")
    for j in rows:
        j_id = j["id"]
        j["events"] = db.q("select msg from events where job_id=? order by id desc limit 8", (j_id,))[::-1]
        j["frontend_url"] = f"/sites/{j_id}/"
        j["backend_api_url"] = f"/api/sites/{j_id}/info"
        j["orders_count"] = (db.one("select count(*) c from site_orders where job_id=?", (j_id,)) or {}).get("c", 0)
    return rows


@app.get("/api/jobs/{jid}")
def get_job_detail(jid: int):
    j = db.one("select * from jobs where id=?", (jid,))
    if not j:
        raise HTTPException(404, "المشروع غير موجود")
    j["events"] = db.q("select ts,msg from events where job_id=? order by id", (jid,))
    j["contracts"] = db.q("select from_agent,to_agent,sha256,preview from contracts where job_id=? order by id", (jid,))
    j["frontend_url"] = f"/sites/{jid}/"
    j["backend_api_url"] = f"/api/sites/{jid}/info"
    j["orders"] = db.q("select * from site_orders where job_id=? order by id desc", (jid,))
    return j


@app.post("/api/jobs/{jid}/decision")
async def job_decision(jid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    decision = body.get("decision", "approve")
    return await corp.decide(jid, decision)


# =========================================================
# Full-Stack Site Endpoints: Frontend + Backend APIs
# =========================================================
@app.get("/sites/{jid}/")
@app.get("/sites/{jid}/index.html")
async def serve_site(jid: int):
    """Serves the complete frontend app for this site, injecting SITE_ID."""
    row = db.one("select html from site_pages where job_id=?", (jid,))
    if not row or not row.get("html"):
        # Check local file fallback
        local_path = os.path.join(corp.SITES, str(jid), "index.html")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                html = f.read()
        else:
            raise HTTPException(404, "لم يتم العثور على موقع هذا المشروع بعد.")
    else:
        html = row["html"]
    
    # Inject SITE_ID javascript so frontend knows its backend endpoint
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


@app.get("/api/sites/{jid}/info")
def site_backend_info(jid: int):
    """Backend API: Returns site metadata, active routes, and gateway status."""
    job = db.one("select * from jobs where id=?", (jid,))
    if not job:
        raise HTTPException(404, "الموقع غير موجود")
    page = db.one("select * from site_pages where job_id=?", (jid,))
    orders_c = (db.one("select count(*) c from site_orders where job_id=?", (jid,)) or {}).get("c", 0)
    items_c = (db.one("select count(*) c from site_items where job_id=?", (jid,)) or {}).get("c", 0)
    
    return {
        "site_id": jid,
        "client": job.get("client"),
        "status": job.get("status"),
        "slug": (page and page.get("slug")) or f"site-{jid}",
        "frontend_url": f"/sites/{jid}/",
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


@app.get("/api/sites/{jid}/items")
def site_backend_items(jid: int):
    """Backend API: Returns menu/services catalog for this site."""
    rows = db.q("select * from site_items where job_id=? order by id", (jid,))
    if rows:
        return rows
    # Fallback to realistic Egyptian SME items
    return [
        {"id": 1, "job_id": jid, "title": "الطلب الكلاسيكي المميز", "price": 65.0, "category": "الأكثر طلباً", "description": "خلطة طازجة خاصة مع صلصة الدقة الأصلية", "badge": "الأكثر طلباً"},
        {"id": 2, "job_id": jid, "title": "كومبو العائلة الفاخر", "price": 220.0, "category": "العروض", "description": "تكفي 4 إلى 5 أفراد مع المشروبات والإضافات", "badge": "توفير"},
        {"id": 3, "job_id": jid, "title": "وجبة التوفير السريعة", "price": 50.0, "category": "الوجبات الفردية", "description": "وجبة مشبعة وسريعة التحضير", "badge": "اقتصادي"}
    ]


@app.post("/api/sites/{jid}/orders")
async def site_backend_place_order(jid: int, body: dict):
    """Backend API: Processes real orders and bookings submitted from the generated frontend."""
    cust_name = str(body.get("customer_name") or "عميل كريم")[:100]
    cust_phone = str(body.get("customer_phone") or "")[:30]
    cust_addr = str(body.get("customer_address") or "استلام من الفرع")[:200]
    items = body.get("items") or []
    total_egp = float(body.get("total_egp") or 0.0)
    pay_method = str(body.get("payment_method") or "cash")[:30]
    
    # Generate authentic Egyptian payment reference
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


@app.get("/api/sites/{jid}/orders")
def site_backend_get_orders(jid: int, x_admin_key: str = Header(default="")):
    return db.q("select * from site_orders where job_id=? order by id desc", (jid,))


# =========================================================
# Company Introspection & Financial Summary
# =========================================================
@app.get("/api/summary")
def get_summary():
    rev = db.one("select coalesce(sum(delta),0) v from ledger where account='client_payment'")
    pay = db.one("select coalesce(sum(delta),0) v from ledger where account like 'payroll:%'")
    rev_v = float(rev["v"]) if rev else 0
    pay_v = -float(pay["v"]) if pay else 0
    
    total_orders = (db.one("select count(*) c from site_orders") or {}).get("c", 0)
    total_sites = (db.one("select count(*) c from site_pages") or {}).get("c", 0)
    
    return {
        "revenue_egp": round(rev_v, 2),
        "payroll_egp": round(pay_v, 3),
        "profit_egp": round(rev_v - pay_v, 2),
        "margin_percent": round(((rev_v - pay_v) / rev_v * 100), 1) if rev_v > 0 else 0,
        "hired_agents": (db.one("select count(*) n from agents") or {"n": 0})["n"],
        "roster_roles": len(roles.all_names()),
        "jobs": (db.one("select count(*) n from jobs") or {"n": 0})["n"],
        "generated_sites": total_sites,
        "total_store_orders": total_orders
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
    
    # 1. /start command
    if text.startswith("/start"):
        await corp.tg_send(
            chat_id,
            "مرحباً بك في AutoCorp 🤖🇪🇬\n"
            "وكالة الذكاء الاصطناعي ذاتية التشغيل للشركات المصرية الناشئة.\n\n"
            "✨ يمكنك طلب موقع فرونت وباك إند كامل من هنا مباشرة!\n"
            "فقط اكتب طلبك، أو أرسل صورة المنيو/الخدمة وسيبدأ الفريق فوراً.\n\n"
            "🛡️ للدخول كمدير مشرف: اكتب الأمر:\n"
            "/admin AlfarouqIbrahim"
        )
        return

    # 2. /admin login command
    if text.startswith("/admin"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip() == admin_pwd:
            os.environ["TELEGRAM_OWNER_CHAT_ID"] = chat_id
            await corp.tg_send(
                chat_id,
                "👑 أهلاً بك يا باشمهندس الفاروق! تم تسجيلك كمدير مشرف على AutoCorp بنجاح.\n"
                "ستصلك قرارات التسعير واعتمادات التسليم هنا لتوافق عليها بضغطة زر."
            )
        else:
            await corp.tg_send(chat_id, "❌ كلمة المرور غير صحيحة.")
        return

    # 3. Client project request (Text or Photo)
    if text or msg.get("photo"):
        check_guardrails(text)
        if msg.get("photo"):
            desc = await corp.tg_image_to_text(msg["photo"][-1]["file_id"], text)
            text = f"{text}\n\n[تحليل صورة العميل بواسطة Vision Analyst]:\n{desc}".strip()
            
        jid = make_job(f"tg:{chat_id}", text, sync=IS_VERCEL)
        if IS_VERCEL:
            try:
                await corp.plan_job(jid)
            except Exception as e:
                print(f"[TG JOB ERR] {e}")
        await corp.tg_send(chat_id, f"🚀 استلمنا طلبك بنجاح! تم فتح مشروع برقم #{jid}، والـ CEO يقود الفريق الآن لتنفيذه.")


@app.post("/telegram")
async def telegram_webhook(req: Request):
    secret = os.getenv("TELEGRAM_SECRET")
    if secret and req.headers.get("x-telegram-bot-api-secret-token") != secret:
        raise HTTPException(401)
    u = await req.json()
    await handle_telegram_update(u)
    return {"ok": True}
