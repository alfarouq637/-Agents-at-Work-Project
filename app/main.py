"""FastAPI application: API routes, Telegram webhook, static serving.

On Vercel (VERCEL=1): no background loop, no local file serving for sites.
Locally: optional tick loop, local sites directory.
"""
import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import corp, db, llm, roles, skills, tools

IS_VERCEL = os.getenv("VERCEL", "0") == "1"


@asynccontextmanager
async def lifespan(_):
    db.init()
    task = None
    secs = int(os.getenv("TICK_SECONDS", "0") or 0)
    if secs > 0 and not IS_VERCEL:
        async def loop():
            while True:
                await asyncio.sleep(secs)
                try:
                    await corp.tick()
                except Exception as e:
                    print("tick error", e)
        task = asyncio.create_task(loop())
    yield
    if task:
        task.cancel()


app = FastAPI(title="AutoCorp - AI agency for Egyptian SMEs", lifespan=lifespan)
BASE = os.path.dirname(os.path.dirname(__file__))

# Mount sites directory only when running locally (not on Vercel)
if not IS_VERCEL:
    os.makedirs(corp.SITES, exist_ok=True)
    app.mount("/sites", StaticFiles(directory=corp.SITES, html=True), name="sites")


def guard(env_names, key):
    need = next((os.getenv(n) for n in env_names if os.getenv(n)), "")
    if need and key != need:
        raise HTTPException(401, "bad key")


def admin(key):
    guard(["ADMIN_KEY"], key)


def make_job(client, request, sync=False):
    jid = db.x("insert into jobs(client,request,status,created_at) values(?,?,?,strftime('%s','now'))",
               ((client or "web-client")[:80], request[:4000], "created"))
    if sync or IS_VERCEL:
        # On Vercel or sync mode, we can't use background tasks
        # Return job_id; caller decides whether to run inline
        return jid
    else:
        corp.spawn(corp.plan_job(jid))
        return jid


@app.get("/")
def home():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


# ----- jobs -----
@app.post("/api/jobs")
async def new_job(body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    req = (body.get("request") or "").strip()
    if not req:
        raise HTTPException(400, "request is required")
    sync = body.get("sync", False) or IS_VERCEL
    jid = make_job(body.get("client"), req, sync=sync)
    if sync:
        # Execute plan + run synchronously within this request
        try:
            await corp.plan_job(jid)
            job = db.one("select * from jobs where id=?", (jid,))
            # If auto-approved (no new hires + below threshold), run it
            if job and job["status"] == "running":
                pass  # plan_job already spawned run_job in non-Vercel
            elif job and job["status"] not in ("awaiting_plan", "rejected", "failed"):
                await corp.run_job(jid)
        except Exception as e:
            print(f"[SYNC JOB ERROR] {e}")
    return {"id": jid}


@app.post("/api/hooks/job")
async def hook_job(body: dict, x_hook_key: str = Header(default="")):
    """Inbound automation: Make / n8n / Zapier / Google Forms / any HTTP client."""
    guard(["HOOK_KEY", "ADMIN_KEY"], x_hook_key)
    req = (body.get("request") or "").strip()
    if not req:
        raise HTTPException(400, "request is required")
    jid = make_job(body.get("client") or "hook", req, sync=IS_VERCEL)
    if IS_VERCEL:
        try:
            await corp.plan_job(jid)
        except Exception as e:
            print(f"[HOOK JOB ERROR] {e}")
    return {"id": jid}


@app.get("/api/jobs")
def jobs():
    rows = db.q("select * from jobs order by id desc limit 20")
    for j in rows:
        j["events"] = db.q("select msg from events where job_id=? order by id desc limit 8", (j["id"],))[::-1]
    return rows


@app.get("/api/jobs/{jid}")
def job(jid: int):
    j = db.one("select * from jobs where id=?", (jid,))
    if not j:
        raise HTTPException(404)
    j["events"] = db.q("select ts,msg from events where job_id=? order by id", (jid,))
    j["contracts"] = db.q("select from_agent,to_agent,sha256 from contracts where job_id=? order by id", (jid,))
    return j


@app.post("/api/jobs/{jid}/decision")
async def job_decision(jid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    return await corp.decide(jid, body.get("decision", "reject"))


# ----- sites (Vercel: serve from DB) -----
@app.get("/sites/{jid}/")
@app.get("/sites/{jid}/index.html")
async def serve_site(jid: int):
    """Serve generated site HTML — from DB on Vercel, filesystem locally."""
    if IS_VERCEL:
        row = db.one("select html from site_pages where job_id=?", (jid,))
        if not row:
            raise HTTPException(404, "Site not found")
        return HTMLResponse(row["html"])
    else:
        path = os.path.join(corp.SITES, str(jid), "index.html")
        if os.path.exists(path):
            return FileResponse(path)
        raise HTTPException(404, "Site not found")


# ----- posts / proposals -----
@app.get("/api/posts")
def posts():
    return db.q("select * from posts order by id desc limit 10")


@app.post("/api/posts/{pid}/decision")
async def post_decision(pid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    return await corp.decide_post(pid, body.get("decision", "reject"))


@app.get("/api/proposals")
def proposals():
    return db.q("select id,kind,target,reason,status,substr(content,1,600) content from proposals order by id desc limit 10")


@app.post("/api/proposals/{pid}/decision")
async def proposal_decision(pid: int, body: dict, x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    d = body.get("decision", "reject")
    return await (corp.rollback_proposal(pid) if d == "rollback" else corp.decide_proposal(pid, d))


# ----- company introspection -----
@app.get("/api/agents")
def agents():
    return db.q("select name,department,origin,uses,round(balance,3) balance from agents order by uses desc, name")


@app.get("/api/roster")
def roster():
    return {"total": len(roles.all_names()), "departments": {d: list(r) for d, r in roles.DEPARTMENTS.items()}}


@app.get("/api/tools")
def list_tools():
    return {k: v[1] for k, v in tools.REGISTRY.items()}


@app.get("/api/skills")
def list_skills():
    return [{"file": s["file"], **s["meta"]} for s in skills.load()]


@app.get("/api/providers")
def list_providers():
    return llm.status()


@app.post("/api/providers/test")
async def test_providers(x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    return await llm.test_all()


@app.get("/api/summary")
def summary():
    rev = db.one("select coalesce(sum(delta),0) v from ledger where account='client_payment'")
    pay = db.one("select coalesce(sum(delta),0) v from ledger where account like 'payroll:%'")
    rev_v = float(rev["v"]) if rev else 0
    pay_v = -float(pay["v"]) if pay else 0
    return {"revenue_egp": round(rev_v, 2), "payroll_egp": round(pay_v, 3), "profit_egp": round(rev_v - pay_v, 2),
            "hired_agents": (db.one("select count(*) n from agents") or {"n": 0})["n"],
            "roster_roles": len(roles.all_names()),
            "jobs": (db.one("select count(*) n from jobs") or {"n": 0})["n"]}


@app.api_route("/api/tick", methods=["GET", "POST"])
async def tick(x_cron_key: str = Header(default=""), key: str = ""):
    guard(["CRON_KEY", "ADMIN_KEY"], x_cron_key or key)
    return await corp.tick()


# ----- Telegram -----
@app.post("/api/telegram/setup")
async def tg_setup(x_admin_key: str = Header(default="")):
    admin(x_admin_key)
    url = os.getenv("PUBLIC_URL", "").rstrip("/")
    if not url:
        raise HTTPException(400, "set PUBLIC_URL (https://...) first")
    async with httpx.AsyncClient(timeout=20) as cl:
        r = await cl.post(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/setWebhook",
                          json={"url": url + "/telegram", "secret_token": os.getenv("TELEGRAM_SECRET", ""),
                                "allowed_updates": ["message", "callback_query"]})
    return r.json()


@app.post("/telegram")
async def telegram(req: Request):
    secret = os.getenv("TELEGRAM_SECRET")
    if secret and req.headers.get("x-telegram-bot-api-secret-token") != secret:
        raise HTTPException(401)
    u = await req.json()
    owner = os.getenv("TELEGRAM_OWNER_CHAT_ID", "")
    cb = u.get("callback_query")
    if cb:
        if str(cb["from"]["id"]) == owner:
            kind, _id = cb["data"].split(":")
            if kind in ("a", "r"):
                await corp.decide(int(_id), "approve" if kind == "a" else "reject")
            elif kind in ("pa", "pr"):
                await corp.decide_post(int(_id), "approve" if kind == "pa" else "reject")
            elif kind in ("pp", "px"):
                await corp.decide_proposal(int(_id), "approve" if kind == "pp" else "reject")
        return {"ok": True}
    msg = u.get("message")
    if msg and str(msg["chat"]["id"]) != owner and (msg.get("text") or msg.get("photo")):
        text = msg.get("text") or msg.get("caption") or ""
        if msg.get("photo"):
            desc = await corp.tg_image_to_text(msg["photo"][-1]["file_id"], text)
            text = f"{text}\n\n[Image analysis]\n{desc}".strip()
        jid = make_job(f"tg:{msg['chat']['id']}", text, sync=IS_VERCEL)
        if IS_VERCEL:
            try:
                await corp.plan_job(jid)
            except Exception as e:
                print(f"[TG JOB ERROR] {e}")
        await corp.tg_send(msg["chat"]["id"], "استلمنا طلبك، الفريق بدأ الشغل 👷")
    return {"ok": True}
