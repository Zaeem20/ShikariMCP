# ShikariMCP — Token-bucket rate limiter for HTTP transport

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


@dataclass
class _TokenBucket:
    """Simple token bucket for one client."""

    tokens: float
    last_refill: float
    capacity: float
    refill_rate: float  # tokens per second

    def consume(self, now: float) -> bool:
        """Try to consume one token. Returns True if allowed."""
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimitMiddleware:
    """ASGI middleware that enforces per-IP token-bucket rate limiting.

    Default: 60 requests/second with burst of 100. Covers all HTTP traffic
    including MCP endpoints, SSE streams, and static responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_second: float = 60.0,
        burst: float = 100.0,
        cleanup_interval: float = 60.0,
    ) -> None:
        self.app = app
        self.requests_per_second = requests_per_second
        self.burst = burst
        self.cleanup_interval = cleanup_interval
        self._buckets: dict[str, _TokenBucket] = {}
        self._last_cleanup: float = time.monotonic()

    def _client_ip(self, scope: Scope) -> str:
        """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        # X-Forwarded-For: first entry is the original client
        xff = headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[0].strip()
        # Use scope's client tuple if available
        client = scope.get("client")
        if client:
            return client[0]
        return "unknown"

    def _get_bucket(self, key: str, now: float) -> _TokenBucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _TokenBucket(
                tokens=self.burst,
                last_refill=now,
                capacity=self.burst,
                refill_rate=self.requests_per_second,
            )
            self._buckets[key] = bucket
        return bucket

    def _maybe_cleanup(self, now: float) -> None:
        """Periodically evict stale buckets to prevent memory growth."""
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now
        stale_threshold = now - (self.burst / self.requests_per_second + 10)
        stale_keys = [
            key for key, bucket in self._buckets.items()
            if bucket.last_refill < stale_threshold
        ]
        for key in stale_keys:
            del self._buckets[key]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        now = time.monotonic()
        client_ip = self._client_ip(scope)

        self._maybe_cleanup(now)
        bucket = self._get_bucket(client_ip, now)

        if not bucket.consume(now):
            retry_after = max(1, int((1.0 - bucket.tokens) / self.requests_per_second) + 1)
            response = PlainTextResponse(
                f"Rate limit exceeded. Retry after {retry_after}s.",
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def create_rate_limiter(
    config: Any,
) -> type[RateLimitMiddleware] | None:
    """Factory that returns a configured rate limiter class, or None if disabled.

    Reads from config.rate_limit_rps and config.rate_limit_burst if present,
    otherwise returns defaults.
    """
    rps = getattr(config, "rate_limit_rps", 60.0)
    burst = getattr(config, "rate_limit_burst", 100.0)

    if rps <= 0:
        return None

    class ConfiguredRateLimiter(RateLimitMiddleware):
        def __init__(self, app: ASGIApp) -> None:
            super().__init__(app, requests_per_second=rps, burst=burst)

    return ConfiguredRateLimiter
