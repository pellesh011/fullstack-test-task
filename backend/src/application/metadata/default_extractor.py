from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


class DefaultMetadataExtractor(MetadataExtractor):
    def extract(self, file: StoredFile, stored_path: Path) -> dict:
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
        }
