"""
Storage Backend Tests
Tests for MemoryStorage and RedisStorage implementations
"""

import pytest
import time
import threading
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rate_limiting.storage import MemoryStorage, RedisStorage


class TestMemoryStorage:
    """Test the in-memory storage backend."""

    def setup_method(self):
        """Set up test fixtures."""
        self.storage = MemoryStorage()

    def teardown_method(self):
        """Clean up after tests."""
        self.storage.clear()

    def test_get_set(self):
        """Test basic get and set operations."""
        assert self.storage.get("key1") is None

        self.storage.set("key1", 100)
        assert self.storage.get("key1") == 100

        self.storage.set("key2", "value")
        assert self.storage.get("key2") == "value"

    def test_set_with_ttl(self):
        """Test setting values with TTL."""
        self.storage.set("expiring_key", "value", ttl=1)
        assert self.storage.get("expiring_key") == "value"

        # Wait for expiry
        time.sleep(1.1)
        assert self.storage.get("expiring_key") is None

    def test_increment(self):
        """Test atomic increment operation."""
        # Increment non-existent key
        result = self.storage.increment("counter")
        assert result == 1

        # Increment existing key
        result = self.storage.increment("counter")
        assert result == 2

        # Increment by custom amount
        result = self.storage.increment("counter", amount=5)
        assert result == 7

    def test_increment_with_ttl(self):
        """Test increment with TTL."""
        self.storage.increment("counter", ttl=1)
        assert self.storage.get("counter") == 1

        time.sleep(1.1)
        assert self.storage.get("counter") is None

    def test_delete(self):
        """Test delete operation."""
        self.storage.set("key", "value")
        assert self.storage.exists("key")

        result = self.storage.delete("key")
        assert result is True
        assert not self.storage.exists("key")

        # Delete non-existent key
        result = self.storage.delete("nonexistent")
        assert result is False

    def test_exists(self):
        """Test exists operation."""
        assert not self.storage.exists("key")

        self.storage.set("key", "value")
        assert self.storage.exists("key")

    def test_get_many(self):
        """Test bulk get operation."""
        self.storage.set("key1", "value1")
        self.storage.set("key2", "value2")

        result = self.storage.get_many(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}

    def test_set_many(self):
        """Test bulk set operation."""
        self.storage.set_many({"key1": "value1", "key2": "value2"})

        assert self.storage.get("key1") == "value1"
        assert self.storage.get("key2") == "value2"

    def test_set_many_with_ttl(self):
        """Test bulk set with TTL."""
        self.storage.set_many({"key1": "value1", "key2": "value2"}, ttl=1)

        assert self.storage.get("key1") == "value1"
        time.sleep(1.1)
        assert self.storage.get("key1") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        self.storage.set("key1", "value1", ttl=1)
        self.storage.set("key2", "value2")  # No TTL

        time.sleep(1.1)

        removed = self.storage.cleanup_expired()
        assert removed == 1

        assert self.storage.get("key1") is None
        assert self.storage.get("key2") == "value2"

    def test_is_available(self):
        """Test availability check."""
        assert self.storage.is_available() is True

    def test_clear(self):
        """Test clear operation."""
        self.storage.set("key1", "value1")
        self.storage.set("key2", "value2")

        self.storage.clear()

        assert self.storage.size() == 0
        assert self.storage.get("key1") is None

    def test_thread_safety(self):
        """Test thread safety of storage operations."""
        errors = []

        def increment_counter():
            try:
                for _ in range(100):
                    self.storage.increment("concurrent_counter")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_counter) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert self.storage.get("concurrent_counter") == 1000


class TestRedisStorageFallback:
    """Test Redis storage with fallback to memory."""

    def test_fallback_when_no_redis_url(self):
        """Test that storage falls back to memory when no Redis URL."""
        storage = RedisStorage(redis_url=None, fallback_to_memory=True)

        assert storage.is_using_fallback() is True
        assert storage.is_available() is True

        # Basic operations should work
        storage.set("key", "value")
        assert storage.get("key") == "value"

    def test_fallback_when_invalid_redis_url(self):
        """Test fallback with invalid Redis URL."""
        storage = RedisStorage(
            redis_url="redis://invalid-host:6379/0", fallback_to_memory=True, connection_timeout=0.1
        )

        assert storage.is_using_fallback() is True

        # Operations should still work via fallback
        storage.set("key", "value")
        assert storage.get("key") == "value"

    def test_no_fallback_raises_error(self):
        """Test that disabling fallback raises error."""
        with pytest.raises(RuntimeError, match="Redis unavailable and fallback disabled"):
            RedisStorage(redis_url=None, fallback_to_memory=False)

    def test_increment_with_fallback(self):
        """Test increment operation with fallback storage."""
        storage = RedisStorage(redis_url=None, fallback_to_memory=True)

        result = storage.increment("counter")
        assert result == 1

        result = storage.increment("counter", amount=5)
        assert result == 6

    def test_get_many_with_fallback(self):
        """Test bulk get with fallback."""
        storage = RedisStorage(redis_url=None, fallback_to_memory=True)

        storage.set("key1", 10)
        storage.set("key2", 20)

        result = storage.get_many(["key1", "key2", "key3"])
        assert result == {"key1": 10.0, "key2": 20.0}

    def test_set_many_with_fallback(self):
        """Test bulk set with fallback."""
        storage = RedisStorage(redis_url=None, fallback_to_memory=True)

        storage.set_many({"key1": 10, "key2": 20})

        assert storage.get("key1") == 10.0
        assert storage.get("key2") == 20.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
