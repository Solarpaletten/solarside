"""In-memory rate limiting and basic abuse protection.

Single-instance design: Solar Core runs as ONE Render web service, so an
in-process store is correct and needs no Redis/extra dependency. If we ever
scale to multiple instances, swap _Store for a Redis-backed implementation
behind the same check_rate_limit() interface.

Strategy: sliding window per identity (api-key + client IP). Each identity may
make at most `limit` requests per `window_seconds`. Older timestamps outside the
window are dropped lazily on each check.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """Sliding-window rate limiter keyed by an arbitrary identity string."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, identity: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds).

        allowed=True  → request may proceed.
        allowed=False → identity is over the limit; retry_after is a hint.
        """
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            q = self._hits[identity]
            # Drop timestamps that have aged out of the window.
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self._limit:
                # Over limit: retry when the oldest hit leaves the window.
                retry_after = max(1, int(self._window - (now - q[0])))
                return False, retry_after
            q.append(now)
            return True, 0

    def prune(self, max_idle_identities: int = 10_000) -> None:
        """Best-effort memory guard: drop empty/idle buckets if the map grows.

        Cheap safety so a flood of unique IPs can't grow the dict forever.
        Called opportunistically, not on a timer.
        """
        if len(self._hits) < max_idle_identities:
            return
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            stale = [k for k, q in self._hits.items() if not q or q[-1] < cutoff]
            for k in stale:
                del self._hits[k]
