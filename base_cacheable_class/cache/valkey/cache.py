import pickle
import re
from typing import Any, cast

from glide import ExpirySet, ExpiryType, FlushMode, GlideClient

from ...interfaces.cache import CacheInterface
from .config import ValkeyClientConfig


class ValkeyCache(CacheInterface):
    _config: ValkeyClientConfig
    _client: GlideClient

    # Recommend initialize with create method, not directly
    def __init__(self, config: ValkeyClientConfig, client: GlideClient):
        self._config = config
        self._client = client

    @classmethod
    async def create(cls, config: ValkeyClientConfig) -> "ValkeyCache":
        client = await GlideClient.create(config.to_glide_config())
        return cls(config, client)

    @property
    def config(self) -> ValkeyClientConfig:
        return self._config

    async def _serialize(self, value: Any) -> bytes:
        data = pickle.dumps(value)
        return data

    async def _deserialize(self, data: bytes | None) -> Any:
        if data is None:
            return None
        data = pickle.loads(data)  # noqa: S301
        return data

    async def get(self, key: str) -> Any:
        data = await self._client.get(key)
        deserialized_data = await self._deserialize(data)
        if deserialized_data is None:
            return None
        if isinstance(deserialized_data, bytes):
            return deserialized_data.decode("utf-8")
        return deserialized_data

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized_value = await self._serialize(value)
        if ttl is not None:
            ttl_ms = int(ttl * 1000)
            expiry = ExpirySet(expiry_type=ExpiryType.MILLSEC, value=ttl_ms)
            await self._client.set(key, serialized_value, expiry=expiry)
        else:
            await self._client.set(key, serialized_value)

    async def exists(self, key: str) -> bool:
        return await self._client.exists([key]) == 1

    async def delete(self, key: str) -> None:
        await self._client.delete([key])

    async def clear(self) -> None:
        await self._client.flushdb(flush_mode=FlushMode.ASYNC)

    async def get_keys(self, pattern: str | None = None) -> list[str]:
        if pattern is None:
            pattern = "*"

        cursor = b"0"
        matched_keys = []
        while True:
            result: list[bytes | list[bytes]] = await self._client.scan(cursor=cursor, match=pattern)
            cursor: bytes = cast(bytes, result[0])
            keys: list[bytes] = cast(list[bytes], result[1])

            decoded_keys = [k.decode() if isinstance(k, bytes) else k for k in keys]
            matched_keys.extend(decoded_keys)

            if cursor == b"0":
                break
        return matched_keys

    async def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        cursor = b"0"
        all_keys: list[str] = []
        while True:
            result: list[bytes | list[bytes]] = await self._client.scan(cursor=cursor, match=f"{target_func_name}*")
            cursor: bytes = cast(bytes, result[0])
            keys: list[bytes] = cast(list[bytes], result[1])

            decoded_keys: list[str] = cast(list[str], [k.decode() if isinstance(k, bytes) else k for k in keys])
            all_keys.extend(decoded_keys)

            if cursor == b"0":
                break
        if not pattern:
            return all_keys

        return [k for k in all_keys if re.compile(pattern).search(k)]

    async def ping(self) -> None:
        await self._client.ping()

    async def close(self) -> None:
        await self._client.close()
