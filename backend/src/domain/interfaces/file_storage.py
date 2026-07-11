from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    @abstractmethod
    async def save(self, stored_name: str, content: bytes) -> Path: ...

    @abstractmethod
    def get_path(self, stored_name: str) -> Path: ...

    @abstractmethod
    async def exists(self, stored_name: str) -> bool: ...

    @abstractmethod
    async def delete(self, stored_name: str) -> bool: ...

    @abstractmethod
    async def read_bytes(self, stored_name: str) -> bytes: ...

    @abstractmethod
    async def read_text(self, stored_name: str) -> str: ...
