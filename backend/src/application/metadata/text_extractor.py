from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


class TextMetadataExtractor(MetadataExtractor):
    def extract(self, file: StoredFile, stored_path: Path) -> dict:
        content = stored_path.read_text(encoding="utf-8", errors="ignore")
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "line_count": len(content.splitlines()),
            "char_count": len(content),
        }
