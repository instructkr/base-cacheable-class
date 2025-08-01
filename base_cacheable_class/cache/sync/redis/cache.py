import pickle
import re
from typing import Any

from redis import Redis

from ..interface import CacheInterface


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

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pickled_value = pickle.dumps(value)
        if ttl is not None:
            self.redis.set(key, pickled_value, ex=ttl)
        else:
            self.redis.set(key, pickled_value)

    def get(self, key: str) -> Any:
        data = self.redis.get(key)
        if data is None:
            return None
        return pickle.loads(data)  # noqa: S301

    def exists(self, key: str) -> bool:
        return bool((self.redis.exists(key)) == 1)

    def delete(self, key: str) -> None:
        self.redis.delete(key)

    def clear(self) -> None:
        self.redis.flushdb()

    def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        cursor: int = 0
        all_keys: list[str] = []

        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=f"{target_func_name}*")
            if keys:
                all_keys.extend(k.decode("utf-8") for k in keys)
            if cursor == 0:
                break

        if not pattern:
            return all_keys

        return [k for k in all_keys if re.compile(pattern).search(k)]

    def get_keys(self, pattern: str | None = None) -> list[str]:
        if not pattern:
            pattern = "*"

        cursor = 0
        matched_keys = []
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=pattern)
            matched_keys.extend(keys)
            if cursor == 0:
                break

        return [k.decode("utf-8") for k in matched_keys]

    def ping(self) -> None:
        self.redis.ping()

    def close(self) -> None:
        self.redis.close()
