"""Caching Mechanism.

This module provides a caching mechanism for reducing API calls.
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Dict, Callable


class Cache:
    """Cache for storing function results.

    This class provides a simple in-memory cache for storing function results.
    It supports time-to-live (TTL) for cache entries.

    Attributes:
        cache: A dictionary of cache entries.
        ttl_seconds: The time-to-live for cache entries in seconds.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize the Cache.

        Args:
            ttl_seconds: The time-to-live for cache entries in seconds.
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value, or None if the key is not in the cache or has expired.
        """
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry["expiry"]:
                return entry["value"]
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)
        self.cache[key] = {"value": value, "expiry": expiry}


def cached(cache_instance: Cache) -> Callable:
    """Decorator for caching function results.

    Args:
        cache_instance: The cache instance to use.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable) -> Callable:
        """Decorator function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments.
                **kwargs: Keyword arguments.

            Returns:
                The function result, either from the cache or by calling the function.
            """
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache_instance.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache_instance.set(key, result)
            return result

        return wrapper

    return decorator
