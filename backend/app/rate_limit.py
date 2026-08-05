"""Minimal in-memory sliding-window rate limiter.

A single-process, in-memory limiter is the right amount of engineering for a
take-home / demo deployment: it needs zero infra and is easy to reason about.
It will not survive multiple worker processes or a restart, which is exactly
the trade-off called out in the README (production would move this to
Redis-backed limiting, e.g. via slowapi + a shared store).
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )
        bucket.append(now)


def client_key(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
