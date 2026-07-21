from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator


class FileStorage(ABC):
    @abstractmethod
    async def save(self, stored_name: str, content: bytes) -> Path: ...

    @abstractmethod
    async def save_stream(
        self, stored_name: str, stream: AsyncGenerator[bytes, None]
    ) -> Path: ...

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

    @abstractmethod
    def read_bytes_stream(
        self, stored_name: str, chunk_size: int = 8192
    ) -> AsyncGenerator[bytes, None]: ...

    @abstractmethod
    def read_text_stream(
        self, stored_name: str, chunk_size: int = 8192
    ) -> AsyncGenerator[str, None]: ...
