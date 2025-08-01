import re
import time
from typing import Any, cast

from ....models import CacheItem
from ..interface import CacheInterface


class InMemoryCache(CacheInterface):
    _instance: "InMemoryCache | None" = None
    cache: dict[str, CacheItem]

    def __new__(cls) -> "InMemoryCache":
        if cls._instance is None:
            cls._instance = cast(InMemoryCache, super().__new__(cls))
            cls._instance.cache = {}
        return cls._instance

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expire_at = time.time() + ttl if ttl is not None else None
        self.cache[key] = CacheItem(value, expire_at)

    async def get(self, key: str) -> Any:
        item = self.cache.get(key)
        if item is None:
            return None
        if item.expire_at is None or time.time() < item.expire_at:
            return item.value
        del self.cache[key]  # Remove expired item
        return None

    async def get_keys(self, pattern: str | None = None) -> list[str]:
        if pattern is None:
            return list(self.cache.keys())

        cache_pattern = re.compile(pattern)
        return [key for key in self.cache if cache_pattern.match(key)]

    async def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        if pattern is None:
            return list(self.cache.keys())

        cache_pattern = re.compile(pattern)
        return [key for key in self.cache if cache_pattern.match(key)]

    async def exists(self, key: str) -> bool:
        item = self.cache.get(key)
        if item is None:
            return False
        if item.expire_at is None or time.time() < item.expire_at:
            return True
        del self.cache[key]  # Remove expired item
        return False

    async def delete(self, key: str) -> None:
        self.cache.pop(key, None)

    async def clear(self) -> None:
        self.cache.clear()
