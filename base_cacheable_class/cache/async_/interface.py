from abc import ABC, abstractmethod
from typing import Any


class CacheInterface(ABC):
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> Any:
        pass

    @abstractmethod
    async def clear(self) -> Any:
        pass

    @abstractmethod
    async def get_keys(self, pattern: str | None = None) -> list[str]:
        pass

    @abstractmethod
    async def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        pass
