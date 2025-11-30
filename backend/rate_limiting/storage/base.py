"""
Abstract Base Storage Interface
Defines the interface for rate limiting storage backends
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseStorage(ABC):
    """
    Abstract base class for rate limiting storage backends.

    All storage implementations must implement these methods
    to be compatible with the rate limiting strategies.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from storage.

        Args:
            key: The storage key

        Returns:
            The stored value, or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in storage.

        Args:
            key: The storage key
            value: The value to store
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Atomically increment a counter.

        Args:
            key: The storage key
            amount: Amount to increment by (default: 1)
            ttl: Time-to-live in seconds for new keys (optional)

        Returns:
            The new value after incrementing
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key from storage.

        Args:
            key: The storage key

        Returns:
            True if key was deleted, False if key didn't exist
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in storage.

        Args:
            key: The storage key

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from storage.

        Args:
            keys: List of storage keys

        Returns:
            Dictionary mapping keys to their values (missing keys omitted)
        """
        pass

    @abstractmethod
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in storage.

        Args:
            mapping: Dictionary of key-value pairs to store
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if all values were set successfully
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the storage backend is available.

        Returns:
            True if storage is available and working
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from storage.

        Returns:
            Number of entries removed
        """
        pass
