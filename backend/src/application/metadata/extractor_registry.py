from src.application.metadata.default_extractor import DefaultMetadataExtractor
from src.application.metadata.pdf_extractor import PdfMetadataExtractor
from src.application.metadata.text_extractor import TextMetadataExtractor
from src.domain.interfaces.metadata_extractor import MetadataExtractor


def get_metadata_extractor(mime_type: str) -> MetadataExtractor:
    if mime_type.startswith("text/"):
        return TextMetadataExtractor()
    if mime_type == "application/pdf":
        return PdfMetadataExtractor()
    return DefaultMetadataExtractor()
