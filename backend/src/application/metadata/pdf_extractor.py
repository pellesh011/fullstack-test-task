import io
from typing import Any

from src.domain.entities.file import File
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.metadata_extractor import MetadataExtractor
from pathlib import Path
from pypdf import PdfReader


class PdfMetadataExtractor(MetadataExtractor):
    @staticmethod
    def can_handle(mime_type: str) -> bool:
        return mime_type == "application/pdf"

    async def extract(self, file: File, storage: FileStorage) -> dict[str, Any]:
        # Read in chunks to avoid loading entire file into memory at once
        # We need to accumulate into a BytesIO for pypdf to read
        buffer = io.BytesIO()
        async for chunk in storage.read_bytes_stream(file.stored_name):
            buffer.write(chunk)
        buffer.seek(0)

        reader = PdfReader(buffer)
        page_count = len(reader.pages)

        return {
            "extension": Path(file.original_name).suffix.lower(),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
            "page_count": page_count,
        }
