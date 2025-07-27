from .in_memory.cache import InMemoryCache
from .in_memory.decorator import InMemoryCacheDecorator
from .redis.cache import RedisCache
from .redis.decorator import RedisCacheDecorator
from .valkey.cache import ValkeyCache
from .valkey.config import ValkeyClientConfig
from .valkey.decorator import ValkeyCacheDecorator


class AsyncCacheDecoratorFactory:
    @classmethod
    async def inmemory(cls, default_ttl: int = 60) -> InMemoryCacheDecorator:
        cache = InMemoryCache()
        return InMemoryCacheDecorator(cache, default_ttl)

    @classmethod
    async def redis(
        cls,
        host: str = "localhost",
        port: int = 6379,
        password: str = "yourpassword",
        username: str = "yourusername",
        db: int = 0,
        socket_timeout: float = 0.5,
        socket_connect_timeout: float = 0.5,
        default_ttl: int = 60,
    ) -> RedisCacheDecorator:
        cache = RedisCache(host, port, password, username, db, socket_timeout, socket_connect_timeout)
        return RedisCacheDecorator(cache, default_ttl)

    @classmethod
    async def valkey(cls, config: ValkeyClientConfig | None = None, default_ttl: int = 60) -> ValkeyCacheDecorator:
        if config is None:
            config = ValkeyClientConfig.localhost()
        cache = await ValkeyCache.create(config)
        return ValkeyCacheDecorator(cache, default_ttl)

    @classmethod
    async def from_inmemory_cache(cls, cache: InMemoryCache, default_ttl: int = 60) -> InMemoryCacheDecorator:
        return InMemoryCacheDecorator(cache, default_ttl)

    @classmethod
    async def from_redis_cache(cls, cache: RedisCache, default_ttl: int = 60) -> RedisCacheDecorator:
        return RedisCacheDecorator(cache, default_ttl)

    @classmethod
    async def from_valkey_cache(cls, cache: ValkeyCache, default_ttl: int = 60) -> ValkeyCacheDecorator:
        return ValkeyCacheDecorator(cache, default_ttl)
