"""Process-local abuse controls for the prototype deployment.

This is intentionally modest: production workers must use the shared Redis
rate-limit design from the remediation plan. Keeping the implementation here
prevents a missing external dependency from silently removing all protection.
"""
from collections import deque
from threading import Lock
import time
from typing import Deque, Dict


class SlidingWindowLimiter:
    """Allow a bounded number of attempts per key in one time window."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            attempts = self._attempts.setdefault(key, deque())
            threshold = now - self.window_seconds
            while attempts and attempts[0] <= threshold:
                attempts.popleft()
            if len(attempts) >= self.limit:
                return False
            attempts.append(now)
            return True

    def reset(self, key: str) -> None:
        """Clear a successful user's failures without exposing attempt details."""
        with self._lock:
            self._attempts.pop(key, None)


# Five attempts in fifteen minutes slows password spraying in a single process.
# Redis-backed limits will replace this when the service is horizontally scaled.
login_limiter = SlidingWindowLimiter(limit=5, window_seconds=15 * 60)
admin_login_limiter = SlidingWindowLimiter(limit=5, window_seconds=15 * 60)
public_order_limiter = SlidingWindowLimiter(limit=20, window_seconds=60 * 60)
upload_limiter = SlidingWindowLimiter(limit=20, window_seconds=60 * 60)
