import asyncio
import magic
from pathlib import Path

from src.application.metadata.default_extractor import DefaultMetadataExtractor
from src.application.metadata.pdf_extractor import PdfMetadataExtractor
from src.application.metadata.text_extractor import TextMetadataExtractor
from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.infrastructure.database.models import StoredFile


def get_extractors() -> list[type[MetadataExtractor]]:
    return [
        DefaultMetadataExtractor,
        TextMetadataExtractor,
        PdfMetadataExtractor,
    ]


async def extract_metadata(file: StoredFile, stored_path: Path) -> dict:
    real_mime = await asyncio.to_thread(magic.from_file, str(stored_path), mime=True)
    result: dict = {}
    for cls in get_extractors():
        if cls.can_handle(real_mime):
            extractor = cls()
            extracted = await extractor.extract(file, stored_path)
            for key, value in extracted.items():
                if key not in result:
                    result[key] = value
    return result
