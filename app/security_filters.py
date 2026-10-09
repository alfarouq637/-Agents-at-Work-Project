"""AutoCorp Security Filters & WAF (Web Application Firewall) Module.

Provides comprehensive protection filters:
1. Input Payload Inspection Filter (WAF against XSS, SQLi, Path Traversal, Command Injection)
2. Content Sanitization & Encoding Filter
3. Defensive HTTP Response Header Filter
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import audit

# High-confidence attack signatures
ATTACK_SIGNATURES: List[Tuple[str, str, re.Pattern]] = [
    (
        "xss_script_tag",
        "Cross-Site Scripting (<script> tag injection)",
        re.compile(r"<\s*script[^>]*>.*?(?:<\s*/\s*script\s*>)?", re.IGNORECASE | re.DOTALL),
    ),
    (
        "xss_event_handler",
        "Cross-Site Scripting (inline event handler injection)",
        re.compile(r"\b(?:onload|onerror|onclick|onmouseover|onfocus)\s*=\s*['\"][^'\"]*?\(", re.IGNORECASE),
    ),
    (
        "xss_javascript_pseudo_protocol",
        "Cross-Site Scripting (javascript: pseudo-protocol)",
        re.compile(r"javascript\s*:\s*[^\s'\"]+", re.IGNORECASE),
    ),
    (
        "sqli_union_select",
        "SQL Injection (UNION SELECT pattern)",
        re.compile(r"\bUNION\s+(?:ALL\s+)?SELECT\b", re.IGNORECASE),
    ),
    (
        "sqli_tautology",
        "SQL Injection (tautology bypass: ' OR '1'='1)",
        re.compile(r"['\"]\s*OR\s+['\"][0-9a-zA-Z]+['\"]\s*=\s*['\"][0-9a-zA-Z]+", re.IGNORECASE),
    ),
    (
        "sqli_drop_table",
        "SQL Injection (destructive DROP/ALTER command)",
        re.compile(r";\s*(?:DROP|ALTER|TRUNCATE)\s+(?:TABLE|DATABASE)\b", re.IGNORECASE),
    ),
    (
        "path_traversal",
        "Path Traversal (directory traversal sequence)",
        re.compile(r"(?:\.\.[/\\]){2,}|(?:\.\.%2f){2,}|%2e%2e%2f", re.IGNORECASE),
    ),
    (
        "command_injection",
        "Remote Command Injection pattern",
        re.compile(r"(?:;\s*(?:rm\s+-rf|cat\s+/etc/passwd|powershell\b|wget\b|curl\s+https?:)|\|\s*(?:bash|sh|nc)\b|\$\([a-zA-Z0-9_\s-]+\))", re.IGNORECASE),
    ),
    (
        "null_byte_injection",
        "Null byte poison attack",
        re.compile(r"\x00|%00"),
    ),
]


def scan_value_for_threats(val: Any, max_depth: int = 5) -> Optional[Tuple[str, str, str]]:
    """Recursively inspect string, list, or dict for malicious attack signatures.
    
    Returns (rule_id, description, snippet) if an attack pattern is detected, else None.
    """
    if max_depth <= 0:
        return None
    if isinstance(val, str):
        # Quick boundary: skip scanning very large payloads or safe base64
        sample = val[:8000]
        for rule_id, desc, pattern in ATTACK_SIGNATURES:
            m = pattern.search(sample)
            if m:
                snippet = sample[max(0, m.start() - 20): min(len(sample), m.end() + 20)]
                return rule_id, desc, snippet
    elif isinstance(val, dict):
        for k, v in val.items():
            res = scan_value_for_threats(k, max_depth - 1) or scan_value_for_threats(v, max_depth - 1)
            if res:
                return res
    elif isinstance(val, (list, tuple)):
        for item in val:
            res = scan_value_for_threats(item, max_depth - 1)
            if res:
                return res
    return None


def sanitize_input_text(text: str) -> str:
    """Sanitize user text input by stripping control characters and dangerous protocol prefixes."""
    if not text:
        return ""
    # Strip null bytes and control chars except newlines and tabs
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text))
    # Neutralize dangerous javascript: protocol prefixes
    clean = re.sub(r"javascript\s*:", "blocked-script:", clean, flags=re.IGNORECASE)
    return clean.strip()


class SecurityFilterMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware enforcing WAF-style input filtering and security headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 1. Skip static assets from inspection
        if not path.startswith("/api/"):
            response = await call_next(request)
            self._apply_security_headers(response)
            return response

        # 2. Inspect path for path traversal or null bytes
        if "../" in path or "..\\" in path or "\x00" in path or "%00" in path:
            audit.record(
                "security_filter.blocked_path",
                actor_type="user",
                target_type="path",
                target_id=path[:100],
                outcome="blocked",
                metadata={"rule": "path_traversal", "desc": "Directory traversal or null byte detected in path"},
            )
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "code": "security_filter_violation",
                    "detail": "تم حظر المسار المشبوه بواسطة فلتر الحماية (Path Traversal / Null Byte Detected)",
                },
            )

        # 3. Inspect query parameters for injection attacks
        for param_name, param_val in request.query_params.items():
            threat = scan_value_for_threats(param_name) or scan_value_for_threats(param_val)
            if threat:
                rule_id, desc, snippet = threat
                audit.record(
                    "security_filter.blocked_query",
                    actor_type="user",
                    target_type="query_param",
                    target_id=param_name[:100],
                    outcome="blocked",
                    metadata={"rule": rule_id, "desc": desc, "path": path[:100]},
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "code": "security_filter_violation",
                        "detail": f"تم حظر الاستعلام بواسطة فلتر الحماية المتقدم (Security Filter: {desc})",
                    },
                )

        response = await call_next(request)
        self._apply_security_headers(response)
        return response

    def _apply_security_headers(self, response: Response) -> None:
        """Inject strict defensive headers."""
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
