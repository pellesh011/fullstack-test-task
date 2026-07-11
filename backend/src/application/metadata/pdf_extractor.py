import aiofiles
from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


class PdfMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return mime_type == "application/pdf"

    async def extract(self, file: StoredFile, stored_path: Path) -> dict:
        async with aiofiles.open(stored_path, "rb") as f:
            content = await f.read()
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "approx_page_count": max(content.count(b"/Type /Page"), 1),
        }