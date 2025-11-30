"""
Rate Limiter Core Tests
Tests for the main RateLimiter class
"""

import pytest
import time
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rate_limiting.limiter import RateLimiter, RateLimitExceeded, get_limiter, reset_limiter
from rate_limiting.config import reset_config


class TestRateLimiter:
    """Test the main RateLimiter class."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        reset_limiter()
        self.limiter = RateLimiter(storage="memory", strategy="fixed_window")

    def teardown_method(self):
        """Clean up after tests."""
        self.limiter.shutdown()
        reset_config()
        reset_limiter()

    def test_check_returns_result(self):
        """Test that check returns a RateLimitResult."""
        result = self.limiter.check("test_key", limit="10/minute")

        assert result.allowed is True
        assert result.limit == 10
        assert result.remaining >= 0
        assert result.reset_time > 0

    def test_check_enforces_limit(self):
        """Test that check enforces the rate limit."""
        for i in range(10):
            result = self.limiter.check("test_key", limit="10/minute")
            assert result.allowed is True

        # 11th request should be blocked
        result = self.limiter.check("test_key", limit="10/minute")
        assert result.allowed is False

    def test_is_allowed_simple_api(self):
        """Test the simplified is_allowed method."""
        assert self.limiter.is_allowed("test_key", limit="5/minute") is True

        for _ in range(4):
            self.limiter.is_allowed("test_key", limit="5/minute")

        assert self.limiter.is_allowed("test_key", limit="5/minute") is False

    def test_get_remaining(self):
        """Test getting remaining requests."""
        for _ in range(3):
            self.limiter.check("test_key", limit="10/minute")

        remaining = self.limiter.get_remaining("test_key", limit="10/minute")
        assert remaining == 7

    def test_different_strategies(self):
        """Test using different strategies."""
        # Fixed window
        fw_limiter = RateLimiter(storage="memory", strategy="fixed_window")
        result = fw_limiter.check("key", limit="10/minute")
        assert result.allowed is True
        fw_limiter.shutdown()

        # Sliding window
        sw_limiter = RateLimiter(storage="memory", strategy="sliding_window")
        result = sw_limiter.check("key", limit="10/minute")
        assert result.allowed is True
        sw_limiter.shutdown()

        # Token bucket
        tb_limiter = RateLimiter(storage="memory", strategy="token_bucket")
        result = tb_limiter.check("key", limit="10/minute")
        assert result.allowed is True
        tb_limiter.shutdown()

    def test_tier_based_limits(self):
        """Test tier-based rate limits."""
        # Free tier has 20 requests/minute
        for i in range(20):
            result = self.limiter.check("user:free", tier="free")
            assert result.allowed is True, f"Request {i+1} should be allowed for free tier"

        result = self.limiter.check("user:free", tier="free")
        assert result.allowed is False

        # Premium tier has 200 requests/minute - should still have capacity
        result = self.limiter.check("user:premium", tier="premium")
        assert result.allowed is True

    def test_parse_limit_formats(self):
        """Test various rate limit string formats."""
        # Test different time periods
        self.limiter.check("key", limit="100/second")
        self.limiter.check("key", limit="100/minute")
        self.limiter.check("key", limit="1000/hour")
        self.limiter.check("key", limit="10000/day")

    def test_parse_limit_invalid_format(self):
        """Test that invalid limit format raises error."""
        with pytest.raises(ValueError, match="Invalid rate limit format"):
            self.limiter.check("key", limit="invalid")

        with pytest.raises(ValueError, match="Invalid rate limit format"):
            self.limiter.check("key", limit="100")

    def test_parse_limit_invalid_period(self):
        """Test that invalid period raises error."""
        with pytest.raises(ValueError, match="Unknown time period"):
            self.limiter.check("key", limit="100/week")

    def test_get_headers(self):
        """Test rate limit header generation."""
        result = self.limiter.check("key", limit="10/minute")
        headers = self.limiter.get_headers(result)

        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

        assert headers["X-RateLimit-Limit"] == "10"

    def test_get_headers_when_blocked(self):
        """Test headers include Retry-After when blocked."""
        for _ in range(10):
            self.limiter.check("key", limit="10/minute")

        result = self.limiter.check("key", limit="10/minute")
        headers = self.limiter.get_headers(result)

        assert "Retry-After" in headers
        assert int(headers["Retry-After"]) > 0

    def test_bypass_with_header(self):
        """Test rate limit bypass with header."""
        import os

        os.environ["RATE_LIMIT_BYPASS_KEY"] = "test-bypass-key"

        reset_config()
        limiter = RateLimiter(storage="memory")

        headers = {"X-RateLimit-Bypass": "test-bypass-key"}
        assert limiter.check_bypass(headers) is True

        headers = {"X-RateLimit-Bypass": "wrong-key"}
        assert limiter.check_bypass(headers) is False

        limiter.shutdown()
        del os.environ["RATE_LIMIT_BYPASS_KEY"]

    def test_is_available(self):
        """Test availability check."""
        assert self.limiter.is_available() is True


class TestRateLimitExceeded:
    """Test the RateLimitExceeded exception."""

    def test_exception_properties(self):
        """Test exception has correct properties."""
        from rate_limiting.strategies import RateLimitResult

        result = RateLimitResult(
            allowed=False, limit=100, remaining=0, reset_time=1700000000, retry_after=30
        )

        exc = RateLimitExceeded(result)

        assert exc.result == result
        assert exc.retry_after == 30
        assert exc.reset_time == 1700000000
        assert "Rate limit exceeded" in str(exc)


class TestGlobalLimiter:
    """Test global limiter functions."""

    def teardown_method(self):
        """Clean up after tests."""
        reset_limiter()
        reset_config()

    def test_get_limiter_creates_singleton(self):
        """Test that get_limiter returns the same instance."""
        limiter1 = get_limiter()
        limiter2 = get_limiter()

        assert limiter1 is limiter2

    def test_reset_limiter(self):
        """Test that reset_limiter creates new instance."""
        limiter1 = get_limiter()
        reset_limiter()
        limiter2 = get_limiter()

        assert limiter1 is not limiter2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
