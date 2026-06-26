"""Tests for HTTP rate limiter middleware."""


import pytest

from shikari.core.rate_limiter import RateLimitMiddleware, _TokenBucket


class TestTokenBucket:
    def test_initial_burst(self):
        bucket = _TokenBucket(tokens=5.0, last_refill=0.0, capacity=5.0, refill_rate=1.0)
        now = 0.0
        for _ in range(5):
            assert bucket.consume(now) is True
        assert bucket.consume(now) is False

    def test_refill_over_time(self):
        bucket = _TokenBucket(tokens=0.0, last_refill=0.0, capacity=5.0, refill_rate=1.0)
        # After 3 seconds, should have 3 tokens
        assert bucket.consume(3.0) is True
        assert bucket.consume(0.0) is False  # back to 0

    def test_does_not_exceed_capacity(self):
        bucket = _TokenBucket(tokens=5.0, last_refill=0.0, capacity=5.0, refill_rate=10.0)
        # After 10 seconds, should still be at capacity (5), not 105
        assert bucket.consume(10.0) is True
        assert bucket.tokens <= 5.0


class TestRateLimitMiddleware:
    def _make_middleware(self, rps=2.0, burst=5.0):
        async def dummy_app(scope, receive, send):
            from starlette.responses import PlainTextResponse
            await PlainTextResponse("ok")(scope, receive, send)

        return RateLimitMiddleware(dummy_app, requests_per_second=rps, burst=burst)

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        mw = self._make_middleware(rps=10.0, burst=10.0)
        scope = {"type": "http", "client": ("1.2.3.4", 1234), "headers": []}

        for _ in range(5):
            response_status = None

            async def send(msg):
                nonlocal response_status
                if msg["type"] == "http.response.start":
                    response_status = msg["status"]

            await mw(scope, None, send)
            assert response_status == 200

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        mw = self._make_middleware(rps=1.0, burst=2.0)
        scope = {"type": "http", "client": ("1.2.3.4", 1234), "headers": []}

        response_status = None
        response_headers = {}

        async def send(msg):
            nonlocal response_status, response_headers
            if msg["type"] == "http.response.start":
                response_status = msg["status"]
                response_headers = dict(msg.get("headers", []))

        # First 2 requests should pass (burst=2)
        await mw(scope, None, send)
        assert response_status == 200
        await mw(scope, None, send)
        assert response_status == 200

        # Third should be rate limited
        await mw(scope, None, send)
        assert response_status == 429

    @pytest.mark.asyncio
    async def test_different_ips_independent(self):
        mw = self._make_middleware(rps=1.0, burst=1.0)

        response_status = None

        async def send(msg):
            nonlocal response_status
            if msg["type"] == "http.response.start":
                response_status = msg["status"]

        # IP1 uses its burst
        scope1 = {"type": "http", "client": ("1.1.1.1", 1234), "headers": []}
        await mw(scope1, None, send)
        assert response_status == 200

        # IP2 should still have its burst
        scope2 = {"type": "http", "client": ("2.2.2.2", 1234), "headers": []}
        await mw(scope2, None, send)
        assert response_status == 200

        # IP1 should be limited now
        await mw(scope1, None, send)
        assert response_status == 429

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self):
        mw = self._make_middleware()
        called = False

        async def dummy_app(scope, receive, send):
            nonlocal called
            called = True

        mw.app = dummy_app
        await mw({"type": "websocket"}, None, None)
        assert called is True

    @pytest.mark.asyncio
    async def test_xff_client_ip(self):
        mw = self._make_middleware(rps=1.0, burst=1.0)

        response_status = None

        async def send(msg):
            nonlocal response_status
            if msg["type"] == "http.response.start":
                response_status = msg["status"]

        # Use X-Forwarded-For
        scope = {
            "type": "http",
            "client": ("10.0.0.1", 1234),
            "headers": [(b"x-forwarded-for", b"203.0.113.50, 70.41.3.18")],
        }
        await mw(scope, None, send)
        assert response_status == 200

        # Same X-FF IP should be limited after burst
        await mw(scope, None, send)
        assert response_status == 429

    @pytest.mark.asyncio
    async def test_429_includes_retry_after(self):
        mw = self._make_middleware(rps=1.0, burst=1.0)
        scope = {"type": "http", "client": ("1.2.3.4", 1234), "headers": []}

        response_headers = {}

        async def send(msg):
            nonlocal response_headers
            if msg["type"] == "http.response.start":
                response_headers = {
                    k.decode(): v.decode() for k, v in msg.get("headers", [])
                }

        # Exhaust burst
        await mw(scope, None, send)
        await mw(scope, None, send)

        # Should get Retry-After header
        await mw(scope, None, send)
        assert "retry-after" in response_headers
