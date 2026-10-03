"""Skills = markdown files in skills/. Header lists who gets the skill and which tools it unlocks."""
import os
import re

DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
os.makedirs(DIR, exist_ok=True)


def _parse(raw):
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    meta, body = {}, raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = [x.strip() for x in v.split(",") if x.strip()]
        body = m.group(2)
    return meta, body.strip()


def load():
    out = []
    for f in sorted(os.listdir(DIR)):
        if f.endswith(".md"):
            with open(os.path.join(DIR, f), encoding="utf-8") as fh:
                meta, body = _parse(fh.read())
            out.append({"file": f, "meta": meta, "body": body})
    return out


def for_agent(name, dept):
    texts, tools = [], set()
    for s in load():
        r = [x.lower() for x in s["meta"].get("roles", [])]
        d = [x.lower() for x in s["meta"].get("departments", [])]
        if "*" in r or name.lower() in r or (dept or "").lower() in d:
            texts.append(f"## {s['file'][:-3]}\n{s['body']}")
            tools.update(s["meta"].get("tools", []))
    return "\n\n".join(texts)[:6000], tools


def save(name, content):
    safe = re.sub(r"[^a-z0-9-]", "-", name.lower())[:40].strip("-") or "skill"
    with open(os.path.join(DIR, safe + ".md"), "w", encoding="utf-8") as f:
        f.write(content[:4000])
    return safe + ".md"
