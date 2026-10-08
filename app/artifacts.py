"""Validation for generated browser artifacts before they become tenant content.

The generator is an untrusted producer, whether its output comes from a
template or a model. These checks are intentionally conservative and form a
release gate; they are not a substitute for a browser sandbox or a full CSP.
"""
import re
from typing import List


MAX_HTML_BYTES = 2 * 1024 * 1024
ALLOWED_EXTERNAL_SCRIPT_ORIGINS = ("https://cdn.tailwindcss.com",)
DISALLOWED_MARKUP = (
    (r"<\s*(?:iframe|object|embed)\b", "embedded active content is not allowed"),
    (r"<\s*base\b", "base URL overrides are not allowed"),
    (r"<meta[^>]+http-equiv\s*=\s*['\"]?refresh", "meta refresh redirects are not allowed"),
    (r"(?:href|src)\s*=\s*['\"]?\s*javascript:", "javascript URLs are not allowed"),
    (r"\b(?:eval|Function)\s*\(", "dynamic JavaScript evaluation is not allowed"),
)
SCRIPT_SRC = re.compile(r"<script[^>]+\bsrc\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)


def validate_site_html(document: str) -> List[str]:
    """Return human-readable release-blocking problems without executing HTML."""
    if not isinstance(document, str) or not document.strip():
        return ["the generated document is empty"]
    if len(document.encode("utf-8")) > MAX_HTML_BYTES:
        return ["the generated document exceeds the 2 MB artifact limit"]

    lowered = document.lower()
    issues: List[str] = []
    if "<!doctype html" not in lowered or "<html" not in lowered:
        issues.append("a complete HTML document is required")
    if 'name="viewport"' not in lowered and "name='viewport'" not in lowered:
        issues.append("a responsive viewport declaration is required")
    if not re.search(r"<html[^>]+\blang\s*=", document, re.IGNORECASE):
        issues.append("an HTML language declaration is required")

    for pattern, message in DISALLOWED_MARKUP:
        if re.search(pattern, document, re.IGNORECASE):
            issues.append(message)
    for source in SCRIPT_SRC.findall(document):
        if not source.startswith(ALLOWED_EXTERNAL_SCRIPT_ORIGINS):
            issues.append("an unapproved external script source was requested")
            break
    return issues
