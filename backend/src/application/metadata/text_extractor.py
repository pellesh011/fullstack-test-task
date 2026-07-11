import aiofiles
from pathlib import Path

from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


class TextMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return mime_type.startswith("text/")

    async def extract(self, file: StoredFile, stored_path: Path) -> dict:
        async with aiofiles.open(
            stored_path, "r", encoding="utf-8", errors="ignore"
        ) as f:
            content = await f.read()
        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "line_count": len(content.splitlines()),
            "char_count": len(content),
        }
