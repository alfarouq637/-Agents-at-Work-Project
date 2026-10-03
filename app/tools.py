"""Tools agents may use. Which agent gets which tool is decided by skills/*.md.
All network tools are guarded (public hosts only / pre-registered webhooks only)."""
import ast
import ipaddress
import json
import operator
import os
import re
import socket
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx

UA = {"User-Agent": "Mozilla/5.0 (AutoCorp agent)"}


def _public(url):
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    try:
        for info in socket.getaddrinfo(u.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except Exception:
        return False
    return True


def _strip(html):
    html = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


async def fetch_url(url):
    async with httpx.AsyncClient(timeout=25, headers=UA, follow_redirects=False) as cl:
        for _ in range(4):
            if not _public(url):
                return "BLOCKED: only public http(s) URLs are allowed."
            r = await cl.get(url)
            if r.is_redirect and r.headers.get("location"):
                url = str(httpx.URL(url).join(r.headers["location"]))
                continue
            return _strip(r.text[:300000])[:6000]
    return "Too many redirects."


async def web_search(query):
    key = os.getenv("TAVILY_API_KEY")
    async with httpx.AsyncClient(timeout=25, headers=UA) as cl:
        if key:
            r = await cl.post("https://api.tavily.com/search", headers={"Authorization": f"Bearer {key}"},
                              json={"query": query, "max_results": 5})
            r.raise_for_status()
            return "\n".join(f"- {x['title']} | {x['url']}\n  {x.get('content', '')[:300]}" for x in r.json().get("results", []))
        r = await cl.get("https://html.duckduckgo.com/html/?q=" + quote(query))
        links = re.findall(r'class="result__a" href="(.*?)">(.*?)</a>', r.text)[:6]
        snips = re.findall(r'class="result__snippet".*?>(.*?)</a>', r.text, re.S)
        out = []
        for i, (href, title) in enumerate(links):
            qs = parse_qs(urlparse(href).query)
            real = unquote(qs["uddg"][0]) if "uddg" in qs else href
            out.append(f"- {_strip(title)} | {real}\n  {_strip(snips[i])[:250] if i < len(snips) else ''}")
        return "\n".join(out) or "No results (DuckDuckGo may be blocking; set TAVILY_API_KEY)."


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg}


def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
        if isinstance(n.op, ast.Pow) and abs(_ev(n.right)) > 10:
            raise ValueError("exponent too large")
        return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.operand))
    raise ValueError("unsupported expression")


async def calc(expression):
    return str(_ev(ast.parse(str(expression), mode="eval").body))


async def send_telegram(text):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_OWNER_CHAT_ID")
    if not token or not chat:
        return "Telegram not configured."
    async with httpx.AsyncClient(timeout=20) as cl:
        await cl.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat, "text": str(text)[:3500]})
    return "sent to owner"


def _hooks():
    out = {}
    for item in os.getenv("OUTBOUND_WEBHOOKS", "").split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v.strip()
    return out


async def webhook(name, payload=None):
    url = _hooks().get(name)
    if not url:
        return f"Unknown webhook '{name}'. Registered: {list(_hooks())}"
    async with httpx.AsyncClient(timeout=25) as cl:
        r = await cl.post(url, json=payload or {})
    return f"webhook '{name}' -> HTTP {r.status_code}"


async def figma_read(file_key):
    token = os.getenv("FIGMA_TOKEN")
    if not token:
        return "FIGMA_TOKEN not set."
    async with httpx.AsyncClient(timeout=30) as cl:
        r = await cl.get(f"https://api.figma.com/v1/files/{file_key}?depth=2", headers={"X-Figma-Token": token})
        r.raise_for_status()
    d = r.json()
    lines = [f"File: {d.get('name')}"]
    for page in d.get("document", {}).get("children", []):
        lines.append(f"Page: {page.get('name')}")
        for fr in page.get("children", [])[:25]:
            b = fr.get("absoluteBoundingBox") or {}
            lines.append(f"  - {fr.get('type')}: {fr.get('name')} ({int(b.get('width', 0))}x{int(b.get('height', 0))})")
    return "\n".join(lines)


REGISTRY = {
    "web_search": (web_search, 'web_search(query): search the web, returns titles, urls, snippets', ["query"]),
    "fetch_url": (fetch_url, 'fetch_url(url): read a public web page as text', ["url"]),
    "calc": (calc, 'calc(expression): exact arithmetic, e.g. "3000*0.4"', ["expression"]),
    "send_telegram": (send_telegram, 'send_telegram(text): message the human owner', ["text"]),
    "webhook": (webhook, 'webhook(name, payload): trigger a registered automation (Make/n8n/Zapier) by name', ["name"]),
    "figma_read": (figma_read, 'figma_read(file_key): read pages/frames of a Figma file (read-only)', ["file_key"]),
}


def instructions(allowed):
    lines = [REGISTRY[t][1] for t in sorted(allowed) if t in REGISTRY]
    return ("# Tools\n" + "\n".join("- " + l for l in lines) +
            '\nTo use a tool reply with ONLY this JSON and nothing else: {"tool":"<name>","args":{...}}. '
            "You will receive the result and may call another tool (max 4 calls in total). "
            "When you have enough, reply with your final answer in plain text (no JSON). "
            "Never invent tool results; cite urls you actually read.")


def parse_call(text):
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t).strip()
    if not t.startswith("{"):
        return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    return d if isinstance(d, dict) and "tool" in d else None


async def run(name, args):
    if name not in REGISTRY:
        return f"Unknown tool {name}"
    fn, _, params = REGISTRY[name]
    try:
        kwargs = {k: args[k] for k in args if k in params or k == "payload"}
        out = await fn(**kwargs)
        return str(out)[:6000]
    except Exception as e:
        return f"Tool error: {e}"
