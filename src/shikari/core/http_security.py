"""ASGI security middleware for Shikari's Streamable HTTP endpoint."""

from __future__ import annotations

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class HostOriginSecurityMiddleware:
    """Reject unexpected Host and Origin headers to prevent DNS rebinding."""

    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: list[str],
        allowed_origins: list[str],
    ) -> None:
        self.app = app
        self.allowed_hosts = allowed_hosts
        self.allowed_origins = allowed_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        host = headers.get("host", "")
        origin = headers.get("origin")

        if not host or not _matches(host, self.allowed_hosts):
            await PlainTextResponse("Invalid Host header", status_code=421)(scope, receive, send)
            return
        if origin and not _matches(origin, self.allowed_origins):
            await PlainTextResponse("Invalid Origin header", status_code=403)(scope, receive, send)
            return

        await self.app(scope, receive, send)


def _matches(value: str, patterns: list[str]) -> bool:
    if not patterns:
        return False
    normalized = value.lower().rstrip("/")
    for pattern in patterns:
        candidate = pattern.lower().rstrip("/")
        if candidate == "*":
            return True
        if candidate.endswith(":*"):
            base = candidate[:-2]
            if normalized == base or normalized.startswith(f"{base}:"):
                return True
        if normalized == candidate:
            return True
    return False
