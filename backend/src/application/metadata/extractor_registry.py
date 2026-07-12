import asyncio
import magic
from typing import Any

from src.application.metadata.default_extractor import DefaultMetadataExtractor
from src.application.metadata.pdf_extractor import PdfMetadataExtractor
from src.application.metadata.text_extractor import TextMetadataExtractor
from src.domain.entities.stored_file import StoredFile
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.metadata_extractor import MetadataExtractor


def get_extractors() -> list[type[MetadataExtractor]]:
    return [
        TextMetadataExtractor,
        PdfMetadataExtractor,
        DefaultMetadataExtractor,
    ]


async def extract_metadata(file: StoredFile, storage: FileStorage) -> dict[str, Any]:
    stored_path = storage.get_path(file.stored_name)
    real_mime = await asyncio.to_thread(magic.from_file, str(stored_path), mime=True)
    result: dict[str, Any] = {}
    for cls in get_extractors():
        if cls.can_handle(real_mime):
            extractor = cls()
            extracted = await extractor.extract(file, storage)
            for key, value in extracted.items():
                if key not in result:
                    result[key] = value
    return result
