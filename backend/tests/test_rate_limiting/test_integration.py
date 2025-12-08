"""
Rate Limiting Integration Tests
Tests for FastAPI decorators and endpoint integration
"""

import pytest
import time
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from rate_limiting import (
    limit,
    limit_by_ip,
    limit_by_user,
    get_limiter,
    reset_limiter,
    RateLimitMiddleware,
)
from rate_limiting.config import reset_config
from rate_limiting.decorators import get_remote_address, get_api_key


# Create test app
app = FastAPI()


@app.get("/test/default")
@limit("5/minute")
async def default_limit_endpoint(request: Request):
    return {"status": "ok"}


@app.get("/test/ip-based")
@limit_by_ip("3/minute")
async def ip_limit_endpoint(request: Request):
    return {"status": "ok"}


@app.get("/test/unlimited")
async def unlimited_endpoint(request: Request):
    return {"status": "ok"}


# Test client
client = TestClient(app)


class TestRateLimitDecorators:
    """Test rate limiting decorators with FastAPI."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        reset_limiter()

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()
        reset_limiter()

    def test_limit_decorator_allows_requests(self):
        """Test that decorator allows requests under limit."""
        for i in range(5):
            response = client.get("/test/default")
            assert response.status_code == 200, f"Request {i+1} should succeed"

    def test_limit_decorator_blocks_excess(self):
        """Test that decorator blocks requests over limit."""
        # Make 5 requests (at limit)
        for _ in range(5):
            client.get("/test/default")

        # 6th request should be blocked
        response = client.get("/test/default")
        assert response.status_code == 429

    def test_429_response_format(self):
        """Test that 429 response has correct format."""
        # Hit the limit
        for _ in range(5):
            client.get("/test/default")

        response = client.get("/test/default")
        assert response.status_code == 429

        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in data
        assert "reset_time" in data
        assert "limit" in data

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        response = client.get("/test/default")

        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers

    def test_retry_after_header_when_blocked(self):
        """Test Retry-After header when rate limited."""
        for _ in range(5):
            client.get("/test/default")

        response = client.get("/test/default")
        assert "retry-after" in response.headers

    def test_unlimited_endpoint(self):
        """Test that non-limited endpoints are not affected."""
        for _ in range(20):
            response = client.get("/test/unlimited")
            assert response.status_code == 200


class TestKeyExtraction:
    """Test key extraction functions."""

    def test_get_remote_address_from_client(self):
        """Test extracting IP from direct client."""

        # Mock request with client
        class MockRequest:
            headers = {}
            client = type("Client", (), {"host": "192.168.1.100"})()

        ip = get_remote_address(MockRequest())
        assert ip == "192.168.1.100"

    def test_get_remote_address_from_forwarded(self):
        """Test extracting IP from X-Forwarded-For."""

        class MockRequest:
            headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
            client = type("Client", (), {"host": "127.0.0.1"})()

        ip = get_remote_address(MockRequest())
        assert ip == "10.0.0.1"

    def test_get_remote_address_from_real_ip(self):
        """Test extracting IP from X-Real-IP."""

        class MockRequest:
            headers = {"X-Real-IP": "10.0.0.2"}
            client = type("Client", (), {"host": "127.0.0.1"})()

        ip = get_remote_address(MockRequest())
        assert ip == "10.0.0.2"

    def test_get_api_key_from_header(self):
        """Test extracting API key from X-API-Key header."""

        class MockRequest:
            headers = {"X-API-Key": "test-api-key-123"}

        key = get_api_key(MockRequest())
        assert key == "test-api-key-123"

    def test_get_api_key_from_bearer(self):
        """Test extracting API key from Authorization Bearer."""

        class MockRequest:
            headers = {"Authorization": "Bearer test-token-456"}

        key = get_api_key(MockRequest())
        assert key == "test-token-456"

    def test_get_api_key_none(self):
        """Test that None is returned when no API key."""

        class MockRequest:
            headers = {}

        key = get_api_key(MockRequest())
        assert key is None


class TestRateLimitMiddleware:
    """Test the rate limit middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        reset_limiter()

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()
        reset_limiter()

    def test_middleware_allows_exempt_paths(self):
        """Test that exempt paths are not rate limited."""
        middleware_app = FastAPI()
        middleware_app.add_middleware(
            RateLimitMiddleware, limit_string="2/minute", exempt_paths=["/health"]
        )

        @middleware_app.get("/health")
        async def health():
            return {"status": "ok"}

        test_client = TestClient(middleware_app)

        # Health endpoint should not be rate limited
        for _ in range(10):
            response = test_client.get("/health")
            assert response.status_code == 200


class TestConcurrentRequests:
    """Test rate limiting under concurrent load."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        reset_limiter()

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()
        reset_limiter()

    def test_concurrent_requests_respect_limit(self):
        """Test that concurrent requests respect the limit."""
        import threading

        concurrent_app = FastAPI()

        @concurrent_app.get("/concurrent")
        @limit("10/minute")
        async def concurrent_endpoint(request: Request):
            return {"status": "ok"}

        concurrent_client = TestClient(concurrent_app)
        results = []
        errors = []

        def make_request():
            try:
                response = concurrent_client.get("/concurrent")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Make 20 concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # Should have exactly 10 successful and 10 rate limited
        success_count = sum(1 for r in results if r == 200)
        limited_count = sum(1 for r in results if r == 429)

        assert success_count == 10
        assert limited_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
