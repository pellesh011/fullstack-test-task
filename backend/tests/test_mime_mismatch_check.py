import pytest

from src.application.scanner.checks.mime_mismatch_check import MimeMismatchCheck
from src.domain.entities.scan_result import ScanResultStatus
from src.domain.entities.stored_file import StoredFile


@pytest.fixture
def check():
    return MimeMismatchCheck()


def _make_file(
    original_name: str,
    mime_type: str = "application/pdf",
    original_mime_type: str | None = None,
) -> StoredFile:
    return StoredFile(
        id="test",
        title="test",
        original_name=original_name,
        stored_name="test",
        mime_type=mime_type,
        original_mime_type=original_mime_type,
        size=100,
    )


class TestMimeMismatchCheck:
    def test_extension_matches(self, check):
        result = check.check(_make_file("doc.pdf", mime_type="application/pdf"))
        assert result is None

    def test_extension_mismatch(self, check):
        result = check.check(_make_file("doc.pdf", mime_type="image/png"))
        assert result is not None
        assert result.status == ScanResultStatus.FAILED
        assert "pdf" in result.message
        assert "image/png" in result.message

    def test_unknown_extension_not_flagged(self, check):
        result = check.check(_make_file("data.xyz", mime_type="application/octet-stream"))
        assert result is None

    def test_no_extension_not_flagged(self, check):
        result = check.check(_make_file("README", mime_type="text/plain"))
        assert result is None

    def test_octet_stream_always_allowed(self, check):
        result = check.check(_make_file("doc.pdf", mime_type="application/octet-stream"))
        assert result is None

    @pytest.mark.parametrize("ext,expected_mime", [
        (".png", "image/png"),
        (".jpg", "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".gif", "image/gif"),
        (".webp", "image/webp"),
        (".svg", "image/svg+xml"),
        (".zip", "application/zip"),
        (".gz", "application/gzip"),
        (".mp3", "audio/mpeg"),
        (".mp4", "video/mp4"),
        (".exe", "application/x-msdownload"),
        (".bat", "text/plain"),
        (".sh", "text/plain"),
        (".py", "text/plain"),
        (".js", "text/javascript"),
        (".json", "application/json"),
        (".html", "text/html"),
        (".doc", "application/msword"),
        (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ])
    def test_matching_extensions_return_none(self, check, ext, expected_mime):
        result = check.check(_make_file(f"file{ext}", mime_type=expected_mime))
        assert result is None, f"expected clean for {ext} with {expected_mime}"

    @pytest.mark.parametrize("ext,wrong_mime", [
        (".pdf", "image/png"),
        (".png", "application/zip"),
        (".mp4", "audio/mpeg"),
        (".zip", "image/jpeg"),
        (".exe", "image/png"),
        (".docx", "text/plain"),
    ])
    def test_extension_mismatch_various(self, check, ext, wrong_mime):
        result = check.check(_make_file(f"file{ext}", mime_type=wrong_mime))
        assert result is not None
        assert result.status == ScanResultStatus.FAILED
        assert ext in result.message
        assert wrong_mime in result.message

    def test_client_mime_mismatch(self, check):
        result = check.check(
            _make_file(
                "doc.pdf",
                mime_type="application/pdf",
                original_mime_type="text/plain",
            )
        )
        assert result is not None
        assert result.status == ScanResultStatus.FAILED
        assert "client declared" in result.message
        assert "text/plain" in result.message

    def test_client_mime_matches(self, check):
        result = check.check(
            _make_file(
                "doc.pdf",
                mime_type="application/pdf",
                original_mime_type="application/pdf",
            )
        )
        assert result is None

    def test_client_mime_none_not_flagged(self, check):
        result = check.check(
            _make_file(
                "doc.pdf",
                mime_type="application/pdf",
                original_mime_type=None,
            )
        )
        assert result is None

    def test_client_mime_octet_stream_not_flagged(self, check):
        result = check.check(
            _make_file(
                "doc.pdf",
                mime_type="application/pdf",
                original_mime_type="application/octet-stream",
            )
        )
        assert result is None

    def test_both_extension_and_client_mismatch(self, check):
        result = check.check(
            _make_file(
                "doc.pdf",
                mime_type="image/png",
                original_mime_type="text/plain",
            )
        )
        assert result is not None
        assert result.status == ScanResultStatus.FAILED
        assert "pdf" in result.message
        assert "image/png" in result.message
        assert "text/plain" in result.message