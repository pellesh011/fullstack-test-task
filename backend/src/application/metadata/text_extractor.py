from typing import Any

from src.domain.entities.file import File
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.metadata_extractor import MetadataExtractor
from pathlib import Path


class TextMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return mime_type.startswith("text/")

    async def extract(self, file: File, storage: FileStorage) -> dict[str, Any]:
        line_count = 0
        char_count = 0
        async for chunk in storage.read_text_stream(file.stored_name):
            line_count += chunk.count("\n")
            char_count += len(chunk)

        # If file doesn't end with newline, the last line is not counted
        # splitlines() doesn't count trailing empty line, so we need to adjust
        # This matches the behavior of content.splitlines()

        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "line_count": line_count,
            "char_count": char_count,
        }
