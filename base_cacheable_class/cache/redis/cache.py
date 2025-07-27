import pickle
import re
from typing import Any

from redis.asyncio import Redis

from ...interfaces import CacheInterface


class RedisCache(CacheInterface):
    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        username: str,
        db: int = 0,
        socket_timeout: float = 0.5,
        socket_connect_timeout: float = 0.5,
    ):
        self.redis = Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            username=username,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pickled_value = pickle.dumps(value)
        if ttl is not None:
            await self.redis.set(key, pickled_value, ex=ttl)
        else:
            await self.redis.set(key, pickled_value)

    async def get(self, key: str) -> Any:
        data = await self.redis.get(key)
        if data is None:
            return None
        return pickle.loads(data)  # noqa: S301

    async def exists(self, key: str) -> bool:
        return bool((await self.redis.exists(key)) == 1)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def clear(self) -> None:
        await self.redis.flushdb()

    async def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        cursor: int = 0
        all_keys: list[str] = []

        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=f"{target_func_name}*")
            if keys:
                all_keys.extend(k.decode("utf-8") for k in keys)
            if cursor == 0:
                break

        if not pattern:
            return all_keys

        return [k for k in all_keys if re.compile(pattern).search(k)]

    async def get_keys(self, pattern: str | None = None) -> list[str]:
        if not pattern:
            pattern = "*"

        cursor = 0
        matched_keys = []
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern)
            matched_keys.extend(keys)
            if cursor == 0:
                break

        return [k.decode("utf-8") for k in matched_keys]

    async def ping(self) -> None:
        await self.redis.ping()

    async def close(self) -> None:
        await self.redis.close()
