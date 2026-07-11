from abc import ABC, abstractmethod
from pathlib import Path

from src.models import StoredFile


class MetadataExtractor(ABC):
    @abstractmethod
    async def extract(self, file: StoredFile, stored_path: Path) -> dict: ...

    @staticmethod
    @abstractmethod
    def can_handle(mime_type: str) -> bool: ...
