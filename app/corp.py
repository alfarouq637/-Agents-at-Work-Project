"""The company: CEO planning, lazy hiring (roster + factory), execution,
QA loop, payroll ledger, hash-chained contracts, approvals, marketing."""
import asyncio
import hashlib
import io
import json
import os
import re
import sqlite3
import time
import zipfile

import httpx

from . import builder, db, llm, roles, skills, tools

RATE = float(os.getenv("SALARY_EGP_PER_1K_TOKENS", "0.8"))
THRESHOLD = float(os.getenv("PLAN_APPROVAL_THRESHOLD_EGP", "2000"))
IS_VERCEL = os.getenv("VERCEL", "0") == "1"
SITES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sites")
if not IS_VERCEL:
    os.makedirs(SITES, exist_ok=True)

_tasks = set()


def spawn(coro):
    """Schedule a coroutine. On Vercel, run it inline instead."""
    if IS_VERCEL:
        # On Vercel, we can't use background tasks; caller must await directly
        # This is a fire-and-forget fallback
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
            else:
                loop.run_until_complete(coro)
        except Exception as e:
            print(f"[SPAWN VERCEL] {e}")
        return
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


def log(job_id, msg):
    try:
        print(f"[job {job_id}] {msg}", flush=True)
    except Exception:
        try:
            safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
            print(f"[job {job_id}] {safe_msg}", flush=True)
        except Exception:
            pass
    try:
        db.x("insert into events(job_id,ts,msg) values(?,?,?)", (job_id, time.time(), msg))
    except Exception:
        pass


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def extract_html(text):
    if not text:
        return None
    # 1. Look for complete <!doctype html ... </html> or <html ... </html>
    doc = re.search(r"(<!doctype html[\s\S]*?</html>)", text, re.IGNORECASE)
    if doc:
        return doc.group(1).strip()
    html_tag = re.search(r"(<html[\s\S]*?</html>)", text, re.IGNORECASE)
    if html_tag:
        return html_tag.group(1).strip()
    # 2. Look for code fences containing html structure
    fences = re.findall(r"```(?:html)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    valid_fences = [f.strip() for f in fences if "<html" in f.lower() or "<body" in f.lower() or "<div" in f.lower()]
    if valid_fences:
        return max(valid_fences, key=len)
    # 3. Fallback to start of <!doctype html or <html
    i = text.lower().find("<!doctype html")
    if i < 0:
        i = text.lower().find("<html")
    return text[i:].strip() if i >= 0 else None


# ---------- Telegram (optional human-in-the-loop) ----------
async def tg_send(chat, text, buttons=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not chat:
        return
    body = {"chat_id": chat, "text": text[:3900]}
    if buttons:
        body["reply_markup"] = {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in buttons]]}
    try:
        async with httpx.AsyncClient(timeout=20) as cl:
            await cl.post(f"https://api.telegram.org/bot{token}/sendMessage", json=body)
    except Exception as e:
        print("telegram error", e)


async def tg_owner(text, buttons=None):
    await tg_send(os.getenv("TELEGRAM_OWNER_CHAT_ID"), text, buttons)


# ---------- Ledger + contracts ----------
def pay(agent, tokens, job_id, memo):
    amt = round(tokens / 1000 * RATE, 4)
    db.x("insert into ledger(ts,account,delta,memo,job_id) values(?,?,?,?,?)",
         (time.time(), f"payroll:{agent}", -amt, memo, job_id))
    db.x("update agents set balance=balance+?, uses=uses+1 where name=?", (amt, agent))
    db.x("update jobs set cost=cost+? where id=?", (amt, job_id))
    return amt


def sign(job_id, from_agent, to_agent, payload):
    prev = db.one("select sha256 from contracts where job_id=? order by id desc limit 1", (job_id,))
    body = json.dumps({"prev": prev["sha256"] if prev else "", "from": from_agent, "to": to_agent,
                       "payload": payload[:4000]}, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(body.encode()).hexdigest()
    db.x("insert into contracts(job_id,from_agent,to_agent,preview,sha256,ts) values(?,?,?,?,?,?)",
         (job_id, from_agent, to_agent, payload[:200], h, time.time()))
    log(job_id, f"Contract {h[:8]} signed: {from_agent} -> {to_agent}")


# ---------- Hiring ----------
def template_prompt(name, dept, mission):
    return (f"You are {name}, in the {dept} department of AutoCorp, an AI agency that serves Egyptian SMEs "
            f"(websites, media, consulting). Mission: {mission}\n"
            "Rules: be specific and actionable; write in the client's language (Egyptian-friendly professional "
            "Arabic if the client writes Arabic); never invent statistics, clients or testimonials; state "
            "assumptions; keep answers under 500 words unless producing code or a full document.")


def exists(name):
    return bool(roles.lookup(name)[0]) or bool(db.one("select 1 x from agents where lower(name)=lower(?)", (name,)))


async def factory_hire(spec, job_id=None):
    name, mission = spec["name"], spec.get("mission", "")
    if db.one("select 1 x from agents where name=?", (name,)):
        return
    fallback = template_prompt(name, "Custom (factory)", mission)
    r = await llm.call(
        "You are the Agent Factory. Write a system prompt for a new AI employee. Output ONLY the prompt text.",
        f"Company: AutoCorp, AI agency for Egyptian SMEs.\nNew role: {name}\nMission: {mission}\n"
        "Include: role, process, output format, quality bar, and a rule against inventing facts.",
        tier="brain", mock=fallback)
    db.x("insert into agents(name,department,system_prompt,origin,created_at) values(?,?,?,?,?)",
         (name, "Custom", r["text"].strip(), "factory", time.time()))
    if job_id:
        pay("Agent Factory", r["tokens"], job_id, f"wrote prompt for new role {name}")
        log(job_id, f"HIRED new role via Agent Factory: {name} (saved for reuse)")


async def ensure_agent(name, job_id=None):
    a = db.one("select * from agents where lower(name)=lower(?)", (name,))
    if a:
        return a
    dept, mission, canon = roles.lookup(name)
    if dept:
        db.x("insert into agents(name,department,system_prompt,origin,created_at) values(?,?,?,?,?)",
             (canon, dept, template_prompt(canon, dept, mission), "roster", time.time()))
        if job_id:
            log(job_id, f"Hired from roster: {canon} ({dept})")
    else:
        await factory_hire({"name": name, "mission": "Handle tasks of this type for the agency."}, job_id)
    return db.one("select * from agents where lower(name)=lower(?)", (name,))


# ---------- Planning ----------
CEO_SYS = (
    "You are the CEO agent of AutoCorp, an AI agency serving Egyptian SMEs with: websites (design, build, deploy), "
    "media/content, and business consulting. Plan the job. Reply with ONLY one JSON object:\n"
    '{"service":"web|media|consulting|other","summary":"...","price_egp":number,'
    '"steps":[{"role":"<role>","task":"<specific task>"}],"new_roles":[{"name":"","mission":""}]}\n'
    "Rules: use roles from the roster; max 6 steps; if no roster role fits, define it in new_roles and use its "
    "name in steps. Price must be realistic for an Egyptian SME in EGP (minimum 500). Legal work is a draft for "
    "lawyer review. Do not include website build/review roles; the system adds them for web jobs."
)


def mock_plan(req):
    r = req.lower()
    if any(k in r for k in ["موقع", "website", "site", "landing", "web", "صفحة"]):
        return {"service": "web", "summary": "Build and deploy a landing page", "price_egp": 3000,
                "steps": [{"role": "Solutions Architect", "task": "Turn the request into a page-by-page brief."},
                          {"role": "Arabic Content Writer", "task": "Write the Arabic copy for each section."}],
                "new_roles": []}
    if any(k in r for k in ["محتوى", "سوشيال", "اعلان", "إعلان", "media", "post", "video", "فيديو"]):
        return {"service": "media", "summary": "Content package", "price_egp": 1800,
                "steps": [{"role": "Creative Director", "task": "Define the concept and tone."},
                          {"role": "Arabic Copywriter", "task": "Write 5 posts."},
                          {"role": "Content Calendar Planner", "task": "Schedule them over 2 weeks."}],
                "new_roles": []}
    return {"service": "consulting", "summary": "Consulting memo", "price_egp": 2500,
            "steps": [{"role": "Business Analyst", "task": "Clarify the problem and metrics."},
                      {"role": "Market Researcher", "task": "List what must be researched and verified."},
                      {"role": "Financial Modeler", "task": "Outline a simple break-even model."}],
            "new_roles": []}


def normalize(plan, request):
    if not isinstance(plan, dict) or not isinstance(plan.get("steps"), list) or not plan["steps"]:
        plan = mock_plan(request)
    if plan.get("service") not in ("web", "media", "consulting", "other"):
        plan["service"] = "other"
    steps = [{"role": str(s.get("role", "")).strip(), "task": str(s.get("task", ""))}
             for s in plan["steps"] if isinstance(s, dict) and s.get("role")][:6]
    if plan["service"] == "web":
        steps = [s for s in steps if s["role"] not in ("Frontend Developer", "Code Reviewer")]
        steps += [{"role": "Frontend Developer", "task": "Build the final single-file website."},
                  {"role": "Code Reviewer", "task": "Review the website."}]
    plan["steps"] = steps
    try:
        plan["price_egp"] = max(500.0, float(plan.get("price_egp", 1500)))
    except Exception:
        plan["price_egp"] = 1500.0
    plan["summary"] = str(plan.get("summary", ""))[:300]
    new, seen = [], set()
    for r in (plan.get("new_roles") or []):
        if isinstance(r, dict) and r.get("name"):
            new.append({"name": str(r["name"]).strip(), "mission": str(r.get("mission", ""))[:200]})
    for s in steps:
        if not any(n["name"].lower() == s["role"].lower() for n in new):
            new.append({"name": s["role"], "mission": s["task"][:200]})
    plan["new_roles"] = [n for n in new if not exists(n["name"]) and not (n["name"].lower() in seen or seen.add(n["name"].lower()))]
    return plan


async def plan_job(job_id):
    try:
        job = db.one("select * from jobs where id=?", (job_id,))
        db.x("update jobs set status='planning' where id=?", (job_id,))
        log(job_id, f"CEO received request from {job['client']}")
        ceo = await ensure_agent("CEO", job_id)
        r = await llm.call(CEO_SYS, f"Roster: {', '.join(roles.all_names())}\nClient: {job['client']}\n"
                           f"Request: {job['request']}", tier="brain",
                           mock=json.dumps(mock_plan(job["request"])))
        pay("CEO", r["tokens"], job_id, "planning")
        plan = normalize(parse_json(r["text"]), job["request"])
        db.x("update jobs set plan=?, price=? where id=?", (json.dumps(plan, ensure_ascii=False), plan["price_egp"], job_id))
        log(job_id, f"CEO plan: {plan['service']} | {len(plan['steps'])} steps | quote {plan['price_egp']:.0f} EGP "
                    f"| new roles: {[n['name'] for n in plan['new_roles']] or 'none'}")
        auto_approve = os.getenv("AUTO_APPROVE", "1") == "1"
        if not auto_approve and (plan["new_roles"] or plan["price_egp"] >= THRESHOLD):
            db.x("update jobs set status='awaiting_plan' where id=?", (job_id,))
            why = "new hire(s)" if plan["new_roles"] else "quote above threshold"
            log(job_id, f"HALT: owner decision needed ({why})")
            await tg_owner(f"Job #{job_id} needs your approval ({why})\n{plan['summary']}\nQuote: {plan['price_egp']:.0f} EGP\n"
                           f"Steps: {', '.join(s['role'] for s in plan['steps'])}",
                           [("✅ Approve", f"a:{job_id}"), ("❌ Reject", f"r:{job_id}")])
        else:
            log(job_id, "Within owner limits or auto-approve: approved")
            spawn(run_job(job_id))
    except Exception as e:
        db.x("update jobs set status='failed' where id=?", (job_id,))
        log(job_id, f"FAILED during planning: {e}")


# ---------- Execution ----------
WEB_RULES = ("Output ONE complete self-contained HTML document starting with <!doctype html> and ending with </html> enclosed in an html code fence. Use Tailwind via "
             "<script src=\"https://cdn.tailwindcss.com\"></script>. Use dir=\"rtl\" lang=\"ar\" if the client is "
             "Arabic. Mobile-first. No external images (use CSS gradients/emoji). Include every section in the brief. "
             "No fake testimonials or invented numbers.")
REVIEW_TASK = ("Review this website HTML for: broken structure, missing sections from the brief, RTL/mobile issues, "
               "invented claims. First line must be exactly 'APPROVED' or 'REJECT: <reasons>'.\n\n")
MOCK_HTML = ("```html\n<!doctype html><html lang=\"ar\" dir=\"rtl\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
             "content=\"width=device-width,initial-scale=1\"><title>AutoCorp demo site</title>"
             "<script src=\"https://cdn.tailwindcss.com\"></script></head><body class=\"p-8 text-center\">"
             "<h1 class=\"text-3xl font-bold\">موقع تجريبي</h1><p>تم إنشاؤه بواسطة فريق AutoCorp</p></body></html>\n```")


async def call_agent(ag, ctx, task, job_id):
    name = ag["name"]
    mock = MOCK_HTML if name == "Frontend Developer" else ("APPROVED" if name == "Code Reviewer"
                                                          else f"[MOCK] {name} output for: {task[:80]}")
    tier = "brain" if ag["department"] in ("Executive", "Custom") else "worker"
    skill_text, wanted = skills.for_agent(name, ag["department"])
    allowed = {t for t in wanted if t in tools.REGISTRY}
    system = ag["system_prompt"] + (f"\n\n# Skills\n{skill_text}" if skill_text else "")
    if allowed:
        system += "\n\n" + tools.instructions(allowed)
    user = f"{ctx}\n\nYOUR TASK: {task}" if ctx else task
    total, text, provider = 0, "", ""
    for i in range(5):
        r = await llm.call(system, user, tier=tier, mock=mock)
        total, text, provider = total + r["tokens"], r["text"], r["provider"]
        call = tools.parse_call(text) if (allowed and i < 4) else None
        if not call or call["tool"] not in allowed:
            break
        out = await tools.run(call["tool"], call.get("args") or {})
        log(job_id, f"{name} used tool {call['tool']}")
        user += f"\n\n[your tool call] {json.dumps(call, ensure_ascii=False)}\n[tool result]\n{out}\n\nContinue: call another tool or give the final answer."
    amt = pay(name, total, job_id, "task")
    log(job_id, f"{name} done via {provider} ({total} tokens, salary {amt:.3f} EGP)")
    return text


async def deploy_netlify(html, job_id):
    token = os.getenv("NETLIFY_TOKEN")
    if not token:
        return None
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("index.html", html)
        async with httpx.AsyncClient(timeout=60) as cl:
            r = await cl.post("https://api.netlify.com/api/v1/sites",
                              headers={"Authorization": f"Bearer {token}", "Content-Type": "application/zip"},
                              content=buf.getvalue())
            r.raise_for_status()
            d = r.json()
            url = d.get("ssl_url") or d.get("url")
            log(job_id, f"Deployed to Netlify: {url}")
            return url
    except Exception as e:
        log(job_id, f"Netlify deploy failed (using local preview): {e}")
        return None


async def run_job(job_id):
    try:
        job = db.one("select * from jobs where id=?", (job_id,))
        plan = json.loads(job["plan"])
        db.x("update jobs set status='running' where id=?", (job_id,))
        for spec in plan.get("new_roles", []):
            await factory_hire(spec, job_id)
        ctx = f"Client: {job['client']}\nRequest: {job['request']}\nPlan: {plan['summary']}"
        outputs, html, prev = [], None, "CEO"
        for step in plan["steps"]:
            role = step["role"]
            ag = await ensure_agent(role, job_id)
            log(job_id, f"{ag['name']} starts: {step['task'][:90]}")
            if ag["name"] == "Frontend Developer":
                text = await call_agent(ag, ctx, step["task"] + "\n\n" + WEB_RULES, job_id)
                html = extract_html(text)
                if html:
                    log(job_id, f"Frontend Developer generated complete HTML ({len(html)} chars)")
                else:
                    log(job_id, "Frontend Developer generated code (parsing HTML document)")
            elif ag["name"] == "Code Reviewer" and html:
                text = await call_agent(ag, "", REVIEW_TASK + html[:12000], job_id)
                if "REJECT" in text.strip()[:30].upper():
                    fb = text.strip()[:500]
                    db.x("insert into feedback(agent,note,ts) values(?,?,?)", ("Frontend Developer", fb, time.time()))
                    db.x("update agents set balance=balance-2 where name='Frontend Developer'")
                    log(job_id, f"QA REJECTED contract. Fine 2 EGP to Frontend Developer. Reason: {fb[:120]}")
                    fe = await ensure_agent("Frontend Developer", job_id)
                    t2 = await call_agent(fe, ctx, "Fix the website using this reviewer feedback:\n" + fb +
                                          "\n\nPrevious HTML:\n" + html[:9000] + "\n\n" + WEB_RULES, job_id)
                    html = extract_html(t2) or html
                    outputs.append({"role": "Frontend Developer (revision)", "text": "Revised after QA feedback."})
            else:
                text = await call_agent(ag, ctx, step["task"], job_id)
            sign(job_id, prev, ag["name"], text)
            prev = ag["name"]
            outputs.append({"role": ag["name"], "text": text if ag["name"] != "Frontend Developer" else "(website HTML saved)"})
            ctx += f"\n\n### {ag['name']}\n{text[:2500]}"
        site_url = None
        # Guarantee rich full-stack Arabic SPA website
        if not html or len(html) < 2500 or "موقع تجريبي" in html:
            job_row = db.one("select * from jobs where id=?", (job_id,))
            settings_row = db.one("select * from site_settings where job_id=?", (job_id,)) or {}
            items_rows = db.q("select * from site_items where job_id=?", (job_id,))
            html = builder.build_site_html(job_id, job_row.get("client") or "", job_row.get("request") or "", settings=settings_row, items=items_rows)
            log(job_id, f"AutoCorp Synthesizer built complete full-stack website ({len(html)} chars)")
            
            # Populate default site_items in DB if empty
            if not items_rows:
                niche = builder.detect_niche((job_row.get("request") or "") + " " + (job_row.get("client") or ""))
                for it in builder.DEFAULT_CATALOGS.get(niche, builder.DEFAULT_CATALOGS["general"]):
                    db.x("insert into site_items(job_id, title, price, category, description, badge, created_at) values(?,?,?,?,?,?,?)",
                         (job_id, it["title"], it["price"], it["category"], it["desc"], it.get("badge", ""), time.time()))

        if html:
            # Store site in DB (works on Vercel) and optionally on filesystem
            db.x("INSERT OR REPLACE INTO site_pages(job_id, html, created_at) VALUES(?,?,?)",
                 (job_id, html, time.time()))

            # Generate modular enterprise files & multi-tenant database
            try:
                from app.enterprise_generator import generate_enterprise_project
                settings = db.one("select * from site_settings where job_id=?", (job_id,)) or {}
                items = db.q("select * from site_items where job_id=? order by id", (job_id,))
                brand = settings.get("brand_name") or f"site_{job_id}"
                ent_files = generate_enterprise_project(
                    job_id=job_id,
                    brand_name=brand,
                    niche=settings.get("category", "general"),
                    slogan=settings.get("slogan", ""),
                    primary_color=settings.get("color_primary", ""),
                    secondary_color=settings.get("color_secondary", ""),
                    items=items,
                    settings=settings
                )

                # 1. Register tenant database in Master DB
                schema_sql = ent_files.get("schema.sql", "")
                initial_json = json.loads(ent_files.get("database.json", "{}"))
                catalog_tables = ["users", "categories", "products", "orders", "promo_codes", "reviews", "store_settings"]
                db.register_tenant_db(job_id, brand, schema_sql, catalog_tables, initial_json)

                # 2. Register database files in site_files table
                db.x("INSERT OR REPLACE INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, 'schema.sql', 'database', ?, '', ?)",
                     (job_id, schema_sql, time.time()))
                db.x("INSERT OR REPLACE INTO site_files (job_id, filename, file_type, content, file_url, created_at) VALUES (?, 'database.json', 'database', ?, '', ?)",
                     (job_id, ent_files.get("database.json", ""), time.time()))

                # 3. Write to disk if not Vercel
                if not IS_VERCEL:
                    d = os.path.join(SITES, str(job_id))
                    os.makedirs(d, exist_ok=True)
                    for rel_p, f_content in ent_files.items():
                        full_p = os.path.join(d, rel_p)
                        os.makedirs(os.path.dirname(full_p), exist_ok=True)
                        with open(full_p, "w", encoding="utf-8") as f_out:
                            f_out.write(f_content)

                    # Physically initialize and seed database.sqlite on disk
                    sqlite_path = os.path.join(d, "database.sqlite")
                    try:
                        conn = sqlite3.connect(sqlite_path)
                        conn.executescript(schema_sql)
                        conn.commit()
                        conn.close()
                    except Exception as sq_err:
                        print(f"[SQLITE INIT ERR] {sq_err}")
            except Exception as ent_err:
                print(f"[ENTERPRISE FILES GEN ERR] {ent_err}")

            site_url = await deploy_netlify(html, job_id) or f"/sites/{job_id}/"
        auto_deliver = os.getenv("AUTO_DELIVER", "1") == "1"
        if auto_deliver:
            db.x("update jobs set result=?, site_url=? where id=?",
                 (json.dumps({"outputs": outputs}, ensure_ascii=False), site_url, job_id))
            await deliver(job_id)
            log(job_id, f"Auto-delivered successfully. Site is LIVE at {site_url or f'/sites/{job_id}/'}")
        else:
            db.x("update jobs set status='awaiting_delivery', result=?, site_url=? where id=?",
                 (json.dumps({"outputs": outputs}, ensure_ascii=False), site_url, job_id))
            job = db.one("select * from jobs where id=?", (job_id,))
            log(job_id, f"HALT: final delivery needs owner approval (cost {job['cost']:.2f} EGP, quote {job['price']:.0f} EGP)")
            await tg_owner(f"Job #{job_id} ready for delivery\nCost {job['cost']:.2f} EGP | Quote {job['price']:.0f} EGP\n"
                           f"{site_url or ''}", [("✅ Deliver", f"a:{job_id}"), ("❌ Reject", f"r:{job_id}")])
    except Exception as e:
        db.x("update jobs set status='failed' where id=?", (job_id,))
        log(job_id, f"FAILED during execution: {e}")


async def deliver(job_id):
    job = db.one("select * from jobs where id=?", (job_id,))
    plan = json.loads(job["plan"])
    db.x("insert into ledger(ts,account,delta,memo,job_id) values(?,?,?,?,?)",
         (time.time(), "client_payment", job["price"], "SIMULATED payment (wire Paymob/Stripe for real)", job_id))
    res = json.loads(job["result"] or "{}")
    res["invoice"] = (f"Invoice #{job_id}\nClient: {job['client']}\nService: {plan['summary']}\n"
                      f"Total: {job['price']:.0f} EGP\nStatus: paid (simulated)")
    db.x("update jobs set status='delivered', result=? where id=?", (json.dumps(res, ensure_ascii=False), job_id))
    log(job_id, f"DELIVERED. Revenue +{job['price']:.0f} EGP, agent payroll {job['cost']:.2f} EGP")
    if str(job["client"]).startswith("tg:"):
        chat_id = job["client"][3:]
        site_url = job.get("site_url") or f"/sites/{job_id}/"
        full_url = f"http://localhost:8000{site_url}" if site_url.startswith("/") else site_url
        msg = (
            f"🎉 ألف مبروك! تم الانتهاء من برمجة وتصميم وتسليم موقعك الإلكتروني بنجاح! 🚀\n\n"
            f"🌐 رابط موقعك المباشر:\n{full_url}\n\n"
            f"✨ المميزات المفعلة في موقعك:\n"
            f"• سلة مشتريات تفاعلية وطلب بضغطة زر.\n"
            f"• بوابات الدفع المصرية: فودافون كاش، إنستاباي، فوري، والدفع عند الاستلام.\n"
            f"• زر تواصل وتأكيد سريع عبر الواتساب.\n"
            f"• تصميم عصري متجاوب بالكامل مع الموبايل.\n\n"
            f"🧾 تفاصيل الفاتورة:\n{res.get('invoice', '')}"
        )
        await tg_send(chat_id, msg)
    await emit("job_delivered", {"job_id": job_id, "client": job["client"], "price_egp": job["price"], "site_url": job["site_url"]})
    spawn(marketing_post(job_id))


async def decide(job_id, decision):
    job = db.one("select * from jobs where id=?", (job_id,))
    if not job:
        return {"error": "no such job"}
    ok = decision == "approve"
    if job["status"] == "awaiting_plan":
        if ok:
            log(job_id, "Owner APPROVED plan")
            spawn(run_job(job_id))
        else:
            db.x("update jobs set status='rejected' where id=?", (job_id,))
            log(job_id, "Owner REJECTED plan")
    elif job["status"] == "awaiting_delivery":
        if ok:
            log(job_id, "Owner APPROVED delivery")
            await deliver(job_id)
        else:
            db.x("update jobs set status='rejected' where id=?", (job_id,))
            log(job_id, "Owner REJECTED delivery")
    else:
        return {"error": f"job is {job['status']}, nothing to decide"}
    return {"ok": True}


# ---------- Marketing + self-improvement ----------
async def marketing_post(job_id):
    try:
        job = db.one("select * from jobs where id=?", (job_id,))
        plan = json.loads(job["plan"])
        ag = await ensure_agent("Case Study Writer", job_id)
        text = await call_agent(
            ag, "", f"Write a short anonymized LinkedIn post (Arabic, then one English line) saying AutoCorp just "
                    f"delivered a {plan['service']} project: {plan['summary']}. Do NOT invent numbers, client names "
                    f"or testimonials. End with a call to action for SMEs.", job_id)
        pid = db.x("insert into posts(job_id,text,status,ts) values(?,?,?,?)", (job_id, text, "pending", time.time()))
        log(job_id, f"Marketing post #{pid} drafted, waiting for owner approval")
        await tg_owner(f"Post #{pid} draft:\n{text[:1500]}", [("✅ Publish", f"pa:{pid}"), ("❌ Drop", f"pr:{pid}")])
    except Exception as e:
        log(job_id, f"Marketing failed: {e}")


async def emit(event, payload):
    """Outbound automation: OUTBOUND_WEBHOOKS="job_delivered=https://hook.make.com/..;post_approved=https://..." """
    try:
        if event in tools._hooks():
            await tools.webhook(event, payload)
        elif event == "post_approved" and os.getenv("MAKE_WEBHOOK_URL"):
            async with httpx.AsyncClient(timeout=20) as cl:
                await cl.post(os.getenv("MAKE_WEBHOOK_URL"), json=payload)
    except Exception as e:
        print("emit error", e)


async def decide_post(pid, decision):
    p = db.one("select * from posts where id=?", (pid,))
    if not p or p["status"] != "pending":
        return {"error": "no pending post"}
    if decision != "approve":
        db.x("update posts set status='dropped' where id=?", (pid,))
        return {"ok": True}
    db.x("update posts set status='approved' where id=?", (pid,))
    await emit("post_approved", {"post_id": pid, "text": p["text"]})
    return {"ok": True}


# ---------- Self-improvement (always goes through owner approval) ----------
async def improve(name):
    a = db.one("select * from agents where lower(name)=lower(?)", (name,))
    if not a:
        return {"proposal": None, "reason": "no such agent"}
    fb = db.q("select note from feedback where agent=? order by id desc limit 5", (a["name"],))
    if not fb or db.one("select 1 x from proposals where target=? and status='pending'", (a["name"],)):
        return {"proposal": None, "reason": "no new feedback or a proposal is already pending"}
    po = await ensure_agent("Prompt Optimizer")
    r = await llm.call(po["system_prompt"],
                       f"Current prompt:\n{a['system_prompt']}\n\nRecent QA rejections:\n- " +
                       "\n- ".join(f["note"] for f in fb) +
                       "\n\nRewrite the prompt so these failures stop. Output ONLY the new prompt.",
                       tier="brain", mock=a["system_prompt"] + "\nExtra rule: re-check the output against the brief before answering.")
    pid = db.x("insert into proposals(kind,target,content,old,reason,status,ts) values(?,?,?,?,?,?,?)",
               ("prompt", a["name"], r["text"].strip(), a["system_prompt"], f"{len(fb)} QA rejections", "pending", time.time()))
    db.x("delete from feedback where agent=?", (a["name"],))
    await tg_owner(f"Proposal #{pid}: improve prompt of {a['name']} ({len(fb)} QA rejections)",
                   [("✅ Apply", f"pp:{pid}"), ("❌ Drop", f"px:{pid}")])
    return {"proposal": pid}


async def propose_skill(name, content, reason):
    pid = db.x("insert into proposals(kind,target,content,old,reason,status,ts) values(?,?,?,?,?,?,?)",
               ("skill", name, content[:4000], "", reason, "pending", time.time()))
    await tg_owner(f"Proposal #{pid}: new skill '{name}' - {reason}", [("✅ Apply", f"pp:{pid}"), ("❌ Drop", f"px:{pid}")])
    return pid


async def decide_proposal(pid, decision):
    p = db.one("select * from proposals where id=?", (pid,))
    if not p or p["status"] != "pending":
        return {"error": "no pending proposal"}
    if decision != "approve":
        db.x("update proposals set status='dropped' where id=?", (pid,))
        return {"ok": True}
    if p["kind"] == "prompt":
        db.x("update agents set system_prompt=? where name=?", (p["content"], p["target"]))
    elif p["kind"] == "skill":
        skills.save(p["target"], p["content"])
    db.x("update proposals set status='applied' where id=?", (pid,))
    return {"ok": True}


async def rollback_proposal(pid):
    p = db.one("select * from proposals where id=? and kind='prompt' and status='applied'", (pid,))
    if not p:
        return {"error": "nothing to roll back"}
    db.x("update agents set system_prompt=? where name=?", (p["old"], p["target"]))
    db.x("update proposals set status='rolled_back' where id=?", (pid,))
    return {"ok": True}


async def tick():
    """Called by the internal loop or by an external scheduler (cron-job.org, Make, n8n, GitHub Actions)."""
    done = []
    for row in db.q("select agent from feedback group by agent limit 2"):
        res = await improve(row["agent"])
        if res.get("proposal"):
            done.append(f"improvement proposal #{res['proposal']} for {row['agent']}")
    if os.getenv("AUTONOMOUS_MARKETING", "0") == "1":
        recent = db.one("select 1 x from posts where ts > ?", (time.time() - 86400,))
        if not recent:
            ag = await ensure_agent("Growth Marketer", 0)
            text = await call_agent(ag, "", "Write one honest LinkedIn/Facebook post (Arabic) inviting Egyptian SMEs to "
                                            "request a website, content package or consulting memo from AutoCorp. "
                                            "No invented numbers or testimonials.", 0)
            pid = db.x("insert into posts(job_id,text,status,ts) values(?,?,?,?)", (0, text, "pending", time.time()))
            await tg_owner(f"Growth post #{pid} draft:\n{text[:1200]}", [("✅ Publish", f"pa:{pid}"), ("❌ Drop", f"pr:{pid}")])
            done.append(f"growth post #{pid}")
    return {"actions": done}


async def tg_image_to_text(file_id, caption=""):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        async with httpx.AsyncClient(timeout=40) as cl:
            f = (await cl.get(f"https://api.telegram.org/bot{token}/getFile", params={"file_id": file_id})).json()
            path = f["result"]["file_path"]
            raw = (await cl.get(f"https://api.telegram.org/file/bot{token}/{path}")).content
        import base64
        url = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
        va = await ensure_agent("Vision Analyst", 0)
        r = await llm.call(va["system_prompt"], f"Client caption: {caption or '(none)'}\nDescribe what is visible and any problem you can see. Say what you cannot tell from the photo.",
                           tier="vision", images=[url], mock="[MOCK] image analysed")
        return r["text"]
    except Exception as e:
        return f"(image could not be analysed: {e})"
