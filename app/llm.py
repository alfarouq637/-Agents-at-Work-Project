"""Provider router: any number of OpenAI-compatible providers, several keys per
provider (comma separated), round-robin rotation, cooldown on 429/401, tiers
(brain / worker / vision) and automatic fallback."""
import os
import time

import httpx

BUILTIN = {  # name: (chat url, key env, default model, default vision model)
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "llama-3.3-70b-versatile", ""),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "NVIDIA_API_KEY", "deepseek-ai/deepseek-v4.1-flash", "meta/llama-3.2-90b-vision-instruct"),
    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY", "gpt-oss-120b", ""),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "MISTRAL_API_KEY", "mistral-small-latest", "mistral-small-latest"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "openrouter/free", "openrouter/free"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY", "gemini-2.0-flash", "gemini-2.0-flash"),
}
DEFAULT_ORDER = {
    "brain": "openrouter,nvidia,groq,mistral,cerebras,gemini,wesam",
    "worker": "openrouter,nvidia,groq,mistral,cerebras,gemini,wesam",
    "vision": "nvidia,openrouter,mistral,gemini",
}
_rr, _cool = {}, {}


def providers():
    """name -> {url, keys[], model, vision}. Env is read on every call."""
    out = {}
    for name, (url, kenv, model, vision) in BUILTIN.items():
        keys = [k.strip() for k in os.getenv(kenv, "").split(",") if k.strip()]
        if keys:
            P = name.upper()
            out[name] = {"url": url, "keys": keys, "model": os.getenv(f"{P}_MODEL", model),
                         "vision": os.getenv(f"{P}_VISION_MODEL", vision)}
    if os.getenv("WESAM_API_URL") and os.getenv("WESAM_API_KEY"):
        out["wesam"] = {"url": os.getenv("WESAM_API_URL"), "keys": [os.getenv("WESAM_API_KEY")],
                        "model": os.getenv("WESAM_MODEL", "default"), "vision": os.getenv("WESAM_VISION_MODEL", "")}
    # EXTRA_PROVIDERS="name|chat_url|key1,key2|model|vision_model;name2|..."  -> unlimited providers
    for item in os.getenv("EXTRA_PROVIDERS", "").split(";"):
        parts = [p.strip() for p in item.split("|")]
        if len(parts) >= 4 and parts[0] and parts[1] and parts[2]:
            out[parts[0]] = {"url": parts[1], "keys": [k for k in parts[2].split(",") if k], "model": parts[3],
                             "vision": parts[4] if len(parts) > 4 else ""}
    return out


def status():
    return [{"name": n, "keys": len(p["keys"]), "model": p["model"], "vision_model": p["vision"] or None}
            for n, p in providers().items()]


def _pick_key(name, keys):
    now = time.time()
    ok = [k for k in keys if _cool.get((name, k), 0) < now]
    if not ok:
        return None
    i = _rr.get(name, 0)
    _rr[name] = i + 1
    return ok[i % len(ok)]


async def _post(cl, p, key, model, messages, max_tokens=6000):
    r = await cl.post(p["url"], headers={"Authorization": f"Bearer {key}"},
                      json={"model": model, "messages": messages, "temperature": 0.4, "max_tokens": max_tokens})
    r.raise_for_status()
    d = r.json()
    text = d["choices"][0]["message"]["content"] or ""
    return text, int((d.get("usage") or {}).get("total_tokens") or 0)


async def call(system, user, tier="worker", mock="", images=None, max_tokens=6000):
    """images: list of data URLs (vision tier)."""
    if os.getenv("MOCK", "0") == "1":
        return {"text": mock or "[MOCK]", "tokens": max(60, len(mock) // 4), "provider": "mock"}
    order = os.getenv(f"ORDER_{tier.upper()}", DEFAULT_ORDER[tier]).split(",")
    P = providers()
    last = None
    async with httpx.AsyncClient(timeout=25) as cl:
        for name in [n.strip() for n in order]:
            p = P.get(name)
            if not p:
                continue
            model = p["vision"] if tier == "vision" else p["model"]
            if not model:
                continue
            key = _pick_key(name, p["keys"])
            if not key:
                continue
            content = user
            if images:
                content = [{"type": "text", "text": user}] + [{"type": "image_url", "image_url": {"url": u}} for u in images]
            try:
                text, tokens = await _post(cl, p, key, model,
                                           [{"role": "system", "content": system}, {"role": "user", "content": content}],
                                           max_tokens=max_tokens)
                return {"text": text, "tokens": tokens or len(system + user + text) // 4, "provider": name}
            except httpx.HTTPStatusError as e:
                last = e
                code = e.response.status_code
                _cool[(name, key)] = time.time() + (3600 if code in (401, 403) else 60 if code == 429 else 20)
            except Exception as e:
                last = e
    if mock and os.getenv("MOCK_FALLBACK", "1") == "1":
        return {"text": mock, "tokens": max(60, len(mock) // 4), "provider": "mock-fallback"}
    raise RuntimeError(f"All providers failed or none configured for tier '{tier}': {last}")


async def test_all():
    res = []
    async with httpx.AsyncClient(timeout=40) as cl:
        for name, p in providers().items():
            for i, key in enumerate(p["keys"]):
                try:
                    await _post(cl, p, key, p["model"], [{"role": "user", "content": "Reply with OK"}], 5)
                    res.append({"provider": name, "key": i + 1, "ok": True})
                except Exception as e:
                    res.append({"provider": name, "key": i + 1, "ok": False, "error": str(e)[:140]})
    return res
