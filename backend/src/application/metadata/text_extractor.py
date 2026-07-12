from typing import Any

from src.domain.entities.stored_file import StoredFile
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.metadata_extractor import MetadataExtractor
from pathlib import Path


class TextMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return mime_type.startswith("text/")

    async def extract(self, file: StoredFile, storage: FileStorage) -> dict[str, Any]:
        content = await storage.read_text(file.stored_name)
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "line_count": len(content.splitlines()),
            "char_count": len(content),
        }
