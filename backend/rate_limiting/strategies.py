"""
Rate Limiting Strategies
Multiple strategies for rate limiting: fixed window, sliding window, and token bucket
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_time: int  # Unix timestamp when limit resets
    retry_after: int = 0  # Seconds until retry is allowed (only set if not allowed)


class RateLimitStrategy(ABC):
    """Abstract base class for rate limiting strategies."""

    @abstractmethod
    def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., user_id, IP)
            limit: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with allowed status and rate limit info
        """
        pass

    @abstractmethod
    def get_current_count(self, key: str, window_seconds: int) -> int:
        """Get the current request count for a key."""
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset the rate limit for a key."""
        pass


class FixedWindowStrategy(RateLimitStrategy):
    """
    Fixed window rate limiting strategy.

    Divides time into fixed windows and counts requests per window.
    Simple but can allow bursts at window boundaries.
    """

    def __init__(self, storage):
        """
        Initialize with a storage backend.

        Args:
            storage: Storage backend implementing BaseStorage interface
        """
        self.storage = storage

    def _get_window_key(self, key: str, window_seconds: int) -> Tuple[str, int]:
        """Get the storage key and reset time for the current window."""
        current_time = int(time.time())
        window_start = (current_time // window_seconds) * window_seconds
        window_key = f"{key}:fixed:{window_start}"
        reset_time = window_start + window_seconds
        return window_key, reset_time

    def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed under fixed window rate limit."""
        window_key, reset_time = self._get_window_key(key, window_seconds)

        # Pre-check count to avoid boundary race; use atomic guard if available
        if hasattr(self.storage, "increment_if_below"):
            current_count, allowed = self.storage.increment_if_below(
                window_key, limit, ttl=window_seconds
            )
            if not allowed:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=max(0, reset_time - int(time.time())),
                )
        else:
            current_raw = self.storage.get(window_key) or 0
            if current_raw >= limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=max(0, reset_time - int(time.time())),
                )
            current_count = self.storage.increment(window_key, ttl=window_seconds)

        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        retry_after = 0 if allowed else reset_time - int(time.time())

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=max(0, retry_after),
        )

    def get_current_count(self, key: str, window_seconds: int) -> int:
        """Get current count for the key in the current window."""
        window_key, _ = self._get_window_key(key, window_seconds)
        count = self.storage.get(window_key)
        return count if count is not None else 0

    def reset(self, key: str) -> None:
        """Reset all windows for a key (removes all related keys)."""
        # In fixed window, we'd need to know the window_seconds to find keys
        # Storage implementation should handle wildcard deletion
        pass


class SlidingWindowStrategy(RateLimitStrategy):
    """
    Sliding window rate limiting strategy.

    Uses a combination of the previous and current window counts
    to provide smoother rate limiting without boundary issues.
    """

    def __init__(self, storage):
        """Initialize with a storage backend."""
        self.storage = storage

    def _get_window_keys(self, key: str, window_seconds: int) -> Tuple[str, str, int, float]:
        """
        Get storage keys for current and previous windows.

        Returns:
            Tuple of (current_key, previous_key, reset_time, weight)
        """
        current_time = time.time()
        current_window = int(current_time // window_seconds) * window_seconds
        previous_window = current_window - window_seconds

        current_key = f"{key}:sliding:{current_window}"
        previous_key = f"{key}:sliding:{previous_window}"
        reset_time = current_window + window_seconds

        # Weight is how far into the current window we are (0.0 to 1.0)
        weight = (current_time - current_window) / window_seconds

        return current_key, previous_key, reset_time, weight

    def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed under sliding window rate limit."""
        current_key, previous_key, reset_time, weight = self._get_window_keys(key, window_seconds)

        # Get counts from both windows (default to 0 if None)
        current_count = self.storage.get(current_key) or 0
        previous_count = self.storage.get(previous_key) or 0

        # Calculate weighted count
        # As we progress through the current window, previous window has less weight
        weighted_count = previous_count * (1 - weight) + current_count

        # Check if adding one more request would exceed the limit
        if weighted_count + 1 > limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=reset_time,
                retry_after=max(1, reset_time - int(time.time())),
            )

        # Increment current window
        new_current = self.storage.increment(current_key, ttl=window_seconds * 2)

        # Recalculate weighted count with new value
        new_weighted = previous_count * (1 - weight) + new_current
        remaining = max(0, int(limit - new_weighted))

        return RateLimitResult(
            allowed=True, limit=limit, remaining=remaining, reset_time=reset_time
        )

    def get_current_count(self, key: str, window_seconds: int) -> int:
        """Get current weighted count for the key."""
        current_key, previous_key, _, weight = self._get_window_keys(key, window_seconds)
        current_count = self.storage.get(current_key) or 0
        previous_count = self.storage.get(previous_key) or 0
        return int(previous_count * (1 - weight) + current_count)

    def reset(self, key: str) -> None:
        """Reset sliding window for a key."""
        pass


class TokenBucketStrategy(RateLimitStrategy):
    """
    Token bucket rate limiting strategy.

    Allows bursting while maintaining a long-term rate limit.
    Tokens are added at a constant rate and consumed per request.
    """

    def __init__(self, storage, burst_size: int = 10):
        """
        Initialize with a storage backend.

        Args:
            storage: Storage backend implementing BaseStorage interface
            burst_size: Maximum tokens that can be accumulated (burst capacity)
        """
        self.storage = storage
        self.burst_size = burst_size

    def _get_bucket_keys(self, key: str) -> Tuple[str, str]:
        """Get storage keys for token count and last update time."""
        return f"{key}:bucket:tokens", f"{key}:bucket:updated"

    def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """
        Check if request is allowed under token bucket rate limit.

        Args:
            limit: Refill rate (tokens per window)
            window_seconds: Time window for the refill rate
        """
        tokens_key, updated_key = self._get_bucket_keys(key)
        current_time = time.time()

        # Calculate token refill rate (tokens per second)
        refill_rate = limit / window_seconds

        # Get current bucket state
        bucket_data = self.storage.get_many([tokens_key, updated_key])
        stored_tokens = bucket_data.get(tokens_key, self.burst_size)
        last_updated = bucket_data.get(updated_key, current_time)

        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - last_updated
        tokens_to_add = time_elapsed * refill_rate

        # Update token count (cap at burst_size)
        current_tokens = min(self.burst_size, stored_tokens + tokens_to_add)

        # Calculate reset time (when bucket will be full)
        tokens_needed = self.burst_size - current_tokens
        refill_time = tokens_needed / refill_rate if refill_rate > 0 else window_seconds
        reset_time = int(current_time + refill_time)

        if current_tokens < 1:
            # Not enough tokens
            retry_after = (
                int((1 - current_tokens) / refill_rate) if refill_rate > 0 else window_seconds
            )
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=reset_time,
                retry_after=max(1, retry_after),
            )

        # Consume one token
        new_tokens = current_tokens - 1

        # Store updated state with long TTL
        ttl = window_seconds * 10  # Keep bucket state for a while
        self.storage.set_many({tokens_key: new_tokens, updated_key: current_time}, ttl=ttl)

        return RateLimitResult(
            allowed=True, limit=limit, remaining=int(new_tokens), reset_time=reset_time
        )

    def get_current_count(self, key: str, window_seconds: int) -> int:
        """Get current token count (inverted - returns requests made, not tokens remaining)."""
        tokens_key, _ = self._get_bucket_keys(key)
        tokens = self.storage.get(tokens_key)
        if tokens is None:
            return 0
        return max(0, self.burst_size - int(tokens))

    def reset(self, key: str) -> None:
        """Reset token bucket to full."""
        tokens_key, updated_key = self._get_bucket_keys(key)
        self.storage.delete(tokens_key)
        self.storage.delete(updated_key)


# Strategy factory
def create_strategy(strategy_name: str, storage, **kwargs) -> RateLimitStrategy:
    """
    Create a rate limiting strategy by name.

    Args:
        strategy_name: One of "fixed_window", "sliding_window", "token_bucket"
        storage: Storage backend instance
        **kwargs: Additional arguments for specific strategies

    Returns:
        RateLimitStrategy instance

    Raises:
        ValueError: If strategy_name is not recognized
    """
    strategies = {
        "fixed_window": FixedWindowStrategy,
        "sliding_window": SlidingWindowStrategy,
        "token_bucket": TokenBucketStrategy,
    }

    if strategy_name not in strategies:
        raise ValueError(
            f"Unknown rate limit strategy: {strategy_name}. "
            f"Available: {list(strategies.keys())}"
        )

    strategy_class = strategies[strategy_name]

    if strategy_name == "token_bucket":
        burst_size = kwargs.get("burst_size", 10)
        return strategy_class(storage, burst_size=burst_size)

    return strategy_class(storage)
