from .base import BaseCacheableClass
from .cache.in_memory import InMemoryCache, InMemoryCacheDecorator
from .interfaces import CacheDecoratorInterface, CacheInterface
from .models import CacheItem

__all__ = [
    "BaseCacheableClass",
    "CacheInterface",
    "CacheDecoratorInterface",
    "CacheItem",
    "InMemoryCache",
    "InMemoryCacheDecorator",
]

# Conditional export for Redis classes
try:
    from .cache.redis import RedisCache, RedisCacheDecorator

    __all__.extend(["RedisCache", "RedisCacheDecorator"])
except ImportError:
    # Redis is optional
    pass

try:
    from .cache.valkey import ValkeyCache, ValkeyCacheDecorator, ValkeyClientConfig

    __all__.extend(["ValkeyCache", "ValkeyCacheDecorator", "ValkeyClientConfig"])
except ImportError:
    # Valkey is optional
    pass
