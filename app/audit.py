"""Minimal structured audit trail for security-relevant application actions.

This is a transitional in-process repository. The event shape is deliberately
stable so it can later publish to an outbox and centralized audit service.
"""
import json
import time
from contextvars import ContextVar, Token
from typing import Any, Dict, Optional

from . import db


_request_id: ContextVar[str] = ContextVar("audit_request_id", default="")


def bind_request_id(request_id: str) -> Token:
    """Bind a validated HTTP request ID to audit events created in this task."""
    return _request_id.set(str(request_id or ""))


def reset_request_id(token: Token) -> None:
    """Clear the request context after a response has been completed."""
    _request_id.reset(token)


def record(
    action: str,
    *,
    actor_id: Optional[int] = None,
    actor_type: str = "user",
    target_type: str = "",
    target_id: str = "",
    outcome: str = "success",
    request_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Append non-secret audit metadata without interrupting the primary action."""
    try:
        db.x(
            """INSERT INTO audit_events
            (occurred_at, actor_type, actor_id, action, target_type, target_id, outcome, request_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(),
                actor_type,
                actor_id,
                action,
                target_type,
                str(target_id),
                outcome,
                str(request_id or _request_id.get() or "")[:80],
                json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":")),
            ),
        )
    except Exception:
        # Audit delivery must be made durable through an outbox before it can
        # participate in transaction success/failure semantics.
        pass
