from typing import Any

from src.domain.entities.stored_file import StoredFile
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.metadata_extractor import MetadataExtractor


class DefaultMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return True

    async def extract(self, file: StoredFile, storage: FileStorage) -> dict[str, Any]:
        return {
            "extension": file.original_name.split(".")[-1].lower()
            if "." in file.original_name
            else "",
            "size_bytes": file.size,
            "mime_type": file.mime_type,
        }
