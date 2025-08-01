from abc import ABC, abstractmethod
from typing import Any


class CacheInterface(ABC):
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> Any:
        pass

    @abstractmethod
    def clear(self) -> Any:
        pass

    @abstractmethod
    def get_keys(self, pattern: str | None = None) -> list[str]:
        pass

    @abstractmethod
    def get_keys_regex(self, target_func_name: str, pattern: str | None = None) -> list[str]:
        pass
