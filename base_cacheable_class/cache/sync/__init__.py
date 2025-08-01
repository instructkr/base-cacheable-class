from .decorator import CacheDecorator
from .in_memory import InMemoryCache
from .interface import CacheInterface

__all__ = ["InMemoryCache", "CacheInterface", "CacheDecorator", "SyncCacheDecoratorFactory"]

# Conditional export for Redis classes
try:
    from .redis.cache import RedisCache

    __all__.extend(["RedisCache"])
except ImportError:
    # Redis is optional
    pass


from ..utils.key_builders import key_builder, pattern_builder


class SyncCacheDecoratorFactory:
    @classmethod
    def in_memory(cls, default_ttl: int = 60) -> CacheDecorator:
        cache = InMemoryCache()
        return CacheDecorator(cache, key_builder=key_builder, pattern_builder=pattern_builder, default_ttl=default_ttl)

    @classmethod
    def redis(
        cls,
        host: str,
        port: int,
        password: str,
        username: str,
        db: int = 0,
        socket_timeout: float = 0.5,
        socket_connect_timeout: float = 0.5,
        default_ttl: int = 60,
    ) -> CacheDecorator:
        cache = RedisCache(
            host=host,
            port=port,
            password=password,
            username=username,
            db=db,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )
        return CacheDecorator(cache, key_builder=key_builder, pattern_builder=pattern_builder, default_ttl=default_ttl)
