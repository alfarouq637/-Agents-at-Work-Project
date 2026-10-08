"""Enforce an aggregate HTTP request-body limit while ASGI streams bytes."""

import re
import uuid

from starlette.responses import JSONResponse

MAX_REQUEST_BODY_BYTES = 12 * 1024 * 1024  # Leaves multipart overhead above 10 MiB uploads.


class RequestBodyLimitMiddleware:
    """Buffer only within a hard ceiling so parsers never see oversized bodies."""

    def __init__(self, app, max_bytes: int = MAX_REQUEST_BODY_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        chunks = []
        received = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            if received + len(chunk) > self.max_bytes:
                request_id = next(
                    (
                        value.decode("latin-1", "ignore")
                        for name, value in scope.get("headers", [])
                        if name.lower() == b"x-request-id"
                        and re.fullmatch(rb"[A-Za-z0-9_-]{8,80}", value)
                    ),
                    uuid.uuid4().hex,
                )
                message_text = f"Request body exceeds the {self.max_bytes}-byte limit"
                response = JSONResponse(
                    {
                        "error": {
                            "code": "request_body_too_large",
                            "message": message_text,
                            "request_id": request_id,
                        },
                        "detail": message_text,
                    },
                    status_code=413,
                    headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            received += len(chunk)
            if chunk:
                chunks.append(chunk)
            if not message.get("more_body", False):
                break

        next_chunk = 0

        async def replay_receive():
            nonlocal next_chunk
            if next_chunk < len(chunks):
                chunk = chunks[next_chunk]
                next_chunk += 1
                return {
                    "type": "http.request",
                    "body": chunk,
                    "more_body": next_chunk < len(chunks),
                }
            if not chunks and next_chunk == 0:
                next_chunk = 1
                return {"type": "http.request", "body": b"", "more_body": False}
            return await receive()

        await self.app(scope, replay_receive, send)
