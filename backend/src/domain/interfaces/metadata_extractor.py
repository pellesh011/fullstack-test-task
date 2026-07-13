from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.file import File
from src.domain.interfaces.file_storage import FileStorage


class MetadataExtractor(ABC):
    @abstractmethod
    async def extract(self, file: File, storage: FileStorage) -> dict[str, Any]: ...

    @staticmethod
    @abstractmethod
    def can_handle(mime_type: str) -> bool: ...
