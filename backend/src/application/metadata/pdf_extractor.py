from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


class PdfMetadataExtractor(MetadataExtractor):
    def extract(self, file: StoredFile, stored_path: Path) -> dict:
        content = stored_path.read_bytes()
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "approx_page_count": max(content.count(b"/Type /Page"), 1),
        }
