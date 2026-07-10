from pathlib import Path

import magic

from src.application.metadata.default_extractor import DefaultMetadataExtractor
from src.application.metadata.pdf_extractor import PdfMetadataExtractor
from src.application.metadata.text_extractor import TextMetadataExtractor
from src.domain.interfaces.metadata_extractor import MetadataExtractor
from src.models import StoredFile


def get_extractors() -> list[type[MetadataExtractor]]:
    return [
        DefaultMetadataExtractor,
        TextMetadataExtractor,
        PdfMetadataExtractor,
    ]


def extract_metadata(file: StoredFile, stored_path: Path) -> dict:
    real_mime = magic.from_file(str(stored_path), mime=True)
    result: dict = {}
    for cls in get_extractors():
        if cls.can_handle(real_mime):
            result.update(cls().extract(file, stored_path))
    return result
