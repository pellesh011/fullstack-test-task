from datetime import datetime

import pytest_asyncio

from src.application.metadata.text_extractor import TextMetadataExtractor
from src.application.metadata.pdf_extractor import PdfMetadataExtractor
from src.domain.entities.file import File
from src.domain.enums import FileStatus
from src.infrastructure.storage.local_file_storage import LocalFileStorage


@pytest_asyncio.fixture
async def storage(tmp_path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path)


def _make_file(stored_name: str, original_name: str, mime_type: str, size: int) -> File:
    return File(
        id="test-id",
        title="test",
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        original_mime_type=mime_type,
        size=size,
        status=FileStatus.NEW,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestTextMetadataExtractor:
    async def test_extract_line_and_char_count(self, storage: LocalFileStorage):
        content = "line1\nline2\nline3\n"
        await storage.save("text.txt", content.encode())
        file = _make_file("text.txt", "doc.txt", "text/plain", len(content))

        extractor = TextMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["line_count"] == 3
        assert result["char_count"] == len(content)
        assert result["extension"] == ".txt"
        assert result["mime_type"] == "text/plain"
        assert result["size_bytes"] == len(content)

    async def test_extract_no_trailing_newline(self, storage: LocalFileStorage):
        content = "line1\nline2"
        await storage.save("notrail.txt", content.encode())
        file = _make_file("notrail.txt", "notrail.txt", "text/plain", len(content))

        extractor = TextMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["line_count"] == 1

    async def test_extract_empty_lines(self, storage: LocalFileStorage):
        content = "\n\n\n"
        await storage.save("empty_lines.txt", content.encode())
        file = _make_file("empty_lines.txt", "empty_lines.txt", "text/plain", 3)

        extractor = TextMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["line_count"] == 3
        assert result["char_count"] == 3

    async def test_extract_single_line(self, storage: LocalFileStorage):
        content = "just one line"
        await storage.save("single.txt", content.encode())
        file = _make_file("single.txt", "single.txt", "text/plain", len(content))

        extractor = TextMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["line_count"] == 0
        assert result["char_count"] == len(content)

    async def test_extract_chunked_read(self, storage: LocalFileStorage):
        content = "A" * 200 + "\n" + "B" * 200
        await storage.save("big.txt", content.encode())
        file = _make_file("big.txt", "big.txt", "text/plain", len(content))

        extractor = TextMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["line_count"] == 1
        assert result["char_count"] == len(content)

    def test_can_handle_text(self):
        assert TextMetadataExtractor.can_handle("text/plain") is True
        assert TextMetadataExtractor.can_handle("text/html") is True

    def test_cannot_handle_non_text(self):
        assert TextMetadataExtractor.can_handle("image/png") is False
        assert TextMetadataExtractor.can_handle("application/pdf") is False


class TestPdfMetadataExtractor:
    async def test_extract_page_count(self, storage: LocalFileStorage):
        from reportlab.pdfgen import canvas

        import io

        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(100, 750, "Page 1")
        c.showPage()
        c.drawString(100, 750, "Page 2")
        c.showPage()
        c.save()

        pdf_bytes = buf.getvalue()
        await storage.save("test.pdf", pdf_bytes)
        file = _make_file("test.pdf", "test.pdf", "application/pdf", len(pdf_bytes))

        extractor = PdfMetadataExtractor()
        result = await extractor.extract(file, storage)

        assert result["page_count"] == 2
        assert result["extension"] == ".pdf"
        assert result["mime_type"] == "application/pdf"
        assert result["size_bytes"] == len(pdf_bytes)

    def test_can_handle_pdf(self):
        assert PdfMetadataExtractor.can_handle("application/pdf") is True

    def test_cannot_handle_non_pdf(self):
        assert PdfMetadataExtractor.can_handle("text/plain") is False
        assert PdfMetadataExtractor.can_handle("image/png") is False
