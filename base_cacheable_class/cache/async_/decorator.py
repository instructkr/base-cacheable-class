import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from ...interfaces import CacheDecoratorInterface
from .interface import CacheInterface
from ..utils.key_builders import default_key, default_pattern

logger = logging.getLogger(__name__)


class CacheDecorator(CacheDecoratorInterface):
    def __init__(self, cache: CacheInterface, key_builder=default_key, pattern_builder=default_pattern, default_ttl: int = 60):
        self.cache = cache
        self.default_ttl = default_ttl
        self._key_builder = key_builder
        self._pattern_builder = pattern_builder

    def __call__(self, ttl: int | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                _key = self._key_builder(func, *args, **kwargs)
                current_ttl = ttl if ttl is not None else self.default_ttl

                try:
                    cached_value = await self.cache.get(_key)
                    if cached_value is not None:
                        return cached_value

                    result = await func(*args, **kwargs)

                    if result is not None:
                        await self.cache.set(_key, result, ttl=current_ttl)

                    return result
                except Exception as e:
                    logger.error(f"Error in cache decorator: {e}")
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate(
        self, target_func_name: str, param_mapping: dict[str, str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    pattern = self._pattern_builder(target_func_name, param_mapping, **kwargs)
                    cached_keys = await self.cache.get_keys(pattern)

                    for cache_key in cached_keys:
                        await self.cache.delete(cache_key)

                except Exception as e:
                    logger.error(f"Error in cache invalidation: {e}")

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate_all(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                _key = self._key_builder(func, *args, **kwargs)
                try:
                    await self.cache.clear()
                except Exception as e:
                    logger.error(f"Error in cache clear: {e}")
                return await func(*args, **kwargs)

            return wrapper

        return decorator
