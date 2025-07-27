import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from ...interfaces import CacheDecoratorInterface, CacheInterface

logger = logging.getLogger(__name__)


class ValkeyCacheDecorator(CacheDecoratorInterface):
    def __init__(self, cache: CacheInterface, default_ttl: int = 60):
        self.cache = cache
        self.default_ttl = default_ttl

    def key_builder(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        arg_str = str(args)
        kwarg_str = str(kwargs) if kwargs else "{}"
        func_name = getattr(func, "__name__", "unknown")
        return f"{func_name}:{arg_str}:{kwarg_str}"

    def __call__(self, ttl: int | None = None) -> Callable[..., Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                _key: str = self.key_builder(func, *args, **kwargs)
                current_ttl: int = ttl if ttl is not None else self.default_ttl

                try:
                    cached_value = await self.cache.get(_key)
                    if cached_value is not None:
                        return cached_value

                    result = await func(*args, **kwargs)
                    if result is not None:
                        await self.cache.set(_key, result, ttl=current_ttl)
                    return result

                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis connection or timeout issue: {e}, falling back.")
                    return await func(*args, **kwargs)

                except Exception as e:
                    logger.error(f"Error in cache decorator: {e}")
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate(
        self, target_func_name: str, param_mapping: dict[str, str] | None = None
    ) -> Callable[..., Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    pattern = rf"{target_func_name}:\(.*\):{{.*}}"

                    if param_mapping:
                        kwargs_patterns: list[str] = [
                            rf".*'{k}':\s*'{v!s}'"
                            for k, v in {
                                t_param: kwargs[s_param]
                                for t_param, s_param in param_mapping.items()
                                if s_param in kwargs
                            }.items()
                        ]
                        pattern = rf"{target_func_name}:\(.*\):{{" + ".*".join(kwargs_patterns) + ".*}"

                    cached_keys: list[str] = await self.cache.get_keys_regex(
                        target_func_name=target_func_name, pattern=pattern
                    )
                    for cache_key in cached_keys:
                        await self.cache.delete(cache_key)

                except Exception as e:
                    logger.error(f"Error in cache invalidation: {e}")

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate_all(self) -> Callable[..., Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    await self.cache.clear()
                except Exception as e:
                    logger.error(f"Error in cache clear: {e}")
                return await func(*args, **kwargs)

            return wrapper

        return decorator
