from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    @abstractmethod
    def save(self, stored_name: str, content: bytes) -> Path: ...

    @abstractmethod
    def get_path(self, stored_name: str) -> Path: ...

    @abstractmethod
    def exists(self, stored_name: str) -> bool: ...

    @abstractmethod
    def delete(self, stored_name: str) -> bool: ...

    @abstractmethod
    def read_bytes(self, stored_name: str) -> bytes: ...

    @abstractmethod
    def read_text(self, stored_name: str) -> str: ...
