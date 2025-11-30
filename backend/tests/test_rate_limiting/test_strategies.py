"""
Rate Limiting Strategy Tests
Tests for fixed window, sliding window, and token bucket strategies
"""

import pytest
import time
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rate_limiting.storage import MemoryStorage
from rate_limiting.strategies import (
    FixedWindowStrategy,
    SlidingWindowStrategy,
    TokenBucketStrategy,
    create_strategy,
    RateLimitResult,
)


class TestFixedWindowStrategy:
    """Test fixed window rate limiting strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.storage = MemoryStorage()
        self.strategy = FixedWindowStrategy(self.storage)

    def teardown_method(self):
        """Clean up after tests."""
        self.storage.clear()

    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        for i in range(5):
            result = self.strategy.check("test_key", limit=10, window_seconds=60)
            assert result.allowed is True
            assert result.limit == 10
            assert result.remaining == 10 - (i + 1)

    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        # Make 10 requests (hit limit)
        for _ in range(10):
            result = self.strategy.check("test_key", limit=10, window_seconds=60)
            assert result.allowed is True

        # 11th request should be blocked
        result = self.strategy.check("test_key", limit=10, window_seconds=60)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after > 0

    def test_separate_keys_have_separate_limits(self):
        """Test that different keys have separate limits."""
        for _ in range(10):
            self.strategy.check("key1", limit=10, window_seconds=60)

        # key1 is at limit
        result = self.strategy.check("key1", limit=10, window_seconds=60)
        assert result.allowed is False

        # key2 should still have requests available
        result = self.strategy.check("key2", limit=10, window_seconds=60)
        assert result.allowed is True

    def test_window_resets(self):
        """Test that limit resets when window expires."""
        # Use 1 second window for quick testing
        for _ in range(5):
            self.strategy.check("test_key", limit=5, window_seconds=1)

        # At limit
        result = self.strategy.check("test_key", limit=5, window_seconds=1)
        assert result.allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        result = self.strategy.check("test_key", limit=5, window_seconds=1)
        assert result.allowed is True

    def test_get_current_count(self):
        """Test getting current request count."""
        for i in range(3):
            self.strategy.check("test_key", limit=10, window_seconds=60)

        count = self.strategy.get_current_count("test_key", window_seconds=60)
        assert count == 3


class TestSlidingWindowStrategy:
    """Test sliding window rate limiting strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.storage = MemoryStorage()
        self.strategy = SlidingWindowStrategy(self.storage)

    def teardown_method(self):
        """Clean up after tests."""
        self.storage.clear()

    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        for i in range(5):
            result = self.strategy.check("test_key", limit=10, window_seconds=60)
            assert result.allowed is True

    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        for _ in range(10):
            result = self.strategy.check("test_key", limit=10, window_seconds=60)
            assert result.allowed is True

        # 11th request should be blocked
        result = self.strategy.check("test_key", limit=10, window_seconds=60)
        assert result.allowed is False

    def test_sliding_behavior(self):
        """Test that sliding window provides smoother rate limiting."""
        # Make 5 requests in first window
        for _ in range(5):
            self.strategy.check("test_key", limit=10, window_seconds=2)

        # Wait half the window
        time.sleep(1.0)

        # Should have partial capacity from previous window
        # Previous window (5 requests) * 0.5 weight = 2.5
        # So we should have about 7-8 more requests available
        allowed_count = 0
        for _ in range(8):
            result = self.strategy.check("test_key", limit=10, window_seconds=2)
            if result.allowed:
                allowed_count += 1

        # Due to sliding nature, we should get several more requests
        assert allowed_count >= 5


class TestTokenBucketStrategy:
    """Test token bucket rate limiting strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.storage = MemoryStorage()
        self.strategy = TokenBucketStrategy(self.storage, burst_size=10)

    def teardown_method(self):
        """Clean up after tests."""
        self.storage.clear()

    def test_allows_burst(self):
        """Test that token bucket allows burst up to bucket size."""
        # Should allow burst_size requests immediately
        for i in range(10):
            result = self.strategy.check("test_key", limit=60, window_seconds=60)
            assert result.allowed is True, f"Request {i+1} should be allowed"

    def test_blocks_after_bucket_empty(self):
        """Test that requests are blocked when bucket is empty."""
        # Drain the bucket
        for _ in range(10):
            self.strategy.check("test_key", limit=60, window_seconds=60)

        # Next request should be blocked (bucket empty)
        result = self.strategy.check("test_key", limit=60, window_seconds=60)
        assert result.allowed is False
        assert result.retry_after > 0

    def test_tokens_refill(self):
        """Test that tokens refill over time."""
        # Drain the bucket
        for _ in range(10):
            self.strategy.check("test_key", limit=60, window_seconds=60)

        # Wait for some tokens to refill (60 tokens/minute = 1 token/second)
        time.sleep(1.1)

        # Should have at least 1 token now
        result = self.strategy.check("test_key", limit=60, window_seconds=60)
        assert result.allowed is True


class TestCreateStrategy:
    """Test strategy factory function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.storage = MemoryStorage()

    def test_create_fixed_window(self):
        """Test creating fixed window strategy."""
        strategy = create_strategy("fixed_window", self.storage)
        assert isinstance(strategy, FixedWindowStrategy)

    def test_create_sliding_window(self):
        """Test creating sliding window strategy."""
        strategy = create_strategy("sliding_window", self.storage)
        assert isinstance(strategy, SlidingWindowStrategy)

    def test_create_token_bucket(self):
        """Test creating token bucket strategy."""
        strategy = create_strategy("token_bucket", self.storage, burst_size=20)
        assert isinstance(strategy, TokenBucketStrategy)
        assert strategy.burst_size == 20

    def test_invalid_strategy_raises(self):
        """Test that invalid strategy name raises error."""
        with pytest.raises(ValueError, match="Unknown rate limit strategy"):
            create_strategy("invalid_strategy", self.storage)


class TestRateLimitResult:
    """Test RateLimitResult dataclass."""

    def test_allowed_result(self):
        """Test creating an allowed result."""
        result = RateLimitResult(allowed=True, limit=100, remaining=95, reset_time=1700000000)
        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 95
        assert result.retry_after == 0

    def test_blocked_result(self):
        """Test creating a blocked result."""
        result = RateLimitResult(
            allowed=False, limit=100, remaining=0, reset_time=1700000000, retry_after=30
        )
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
