"""
In-Memory Storage Backend
Thread-safe in-memory storage for rate limiting (development/testing)
"""

import threading
import time
from typing import Dict, List, Optional, Any
from .base import BaseStorage


class MemoryStorage(BaseStorage):
    """
    Thread-safe in-memory storage backend for rate limiting.

    Suitable for single-instance deployments, development, and testing.
    For distributed systems, use RedisStorage instead.
    """

    def __init__(self):
        """Initialize the memory storage."""
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._expiry:
            return False
        return time.time() > self._expiry[key]

    def _cleanup_key(self, key: str) -> None:
        """Remove a key and its expiry if it exists."""
        self._data.pop(key, None)
        self._expiry.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from storage."""
        with self._lock:
            if self._is_expired(key):
                self._cleanup_key(key)
                return None
            return self._data.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in storage."""
        with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
            elif key in self._expiry:
                del self._expiry[key]
            return True

    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment a counter."""
        with self._lock:
            # Check if key exists and is not expired
            if self._is_expired(key):
                self._cleanup_key(key)

            current = self._data.get(key, 0)
            if not isinstance(current, (int, float)):
                current = 0

            new_value = int(current) + amount
            self._data[key] = new_value

            # Set or update TTL
            if ttl is not None:
                # Only set TTL if key is new or TTL is not already set
                if key not in self._expiry:
                    self._expiry[key] = time.time() + ttl

            return new_value

    def delete(self, key: str) -> bool:
        """Delete a key from storage."""
        with self._lock:
            existed = key in self._data
            self._cleanup_key(key)
            return existed

    def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        with self._lock:
            if self._is_expired(key):
                self._cleanup_key(key)
                return False
            return key in self._data

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from storage."""
        result = {}
        with self._lock:
            for key in keys:
                if not self._is_expired(key) and key in self._data:
                    result[key] = self._data[key]
                elif self._is_expired(key):
                    self._cleanup_key(key)
        return result

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in storage."""
        with self._lock:
            expiry_time = time.time() + ttl if ttl else None
            for key, value in mapping.items():
                self._data[key] = value
                if expiry_time:
                    self._expiry[key] = expiry_time
                elif key in self._expiry:
                    del self._expiry[key]
            return True

    def is_available(self) -> bool:
        """Check if storage is available (always True for memory)."""
        return True

    def cleanup_expired(self) -> int:
        """Remove expired entries from storage."""
        removed = 0
        current_time = time.time()
        with self._lock:
            expired_keys = [key for key, expiry in self._expiry.items() if current_time > expiry]
            for key in expired_keys:
                self._cleanup_key(key)
                removed += 1
        return removed

    def clear(self) -> None:
        """Clear all data from storage (useful for testing)."""
        with self._lock:
            self._data.clear()
            self._expiry.clear()

    def size(self) -> int:
        """Get the number of keys in storage."""
        with self._lock:
            return len(self._data)
