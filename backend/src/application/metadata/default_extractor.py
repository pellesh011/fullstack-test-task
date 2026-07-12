from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.infrastructure.database.models import StoredFile


class DefaultMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return True

    async def extract(self, file: StoredFile, stored_path: Path) -> dict:
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
        }
