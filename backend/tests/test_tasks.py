from unittest.mock import patch

import pytest
import src.service as svc
from sqlalchemy import select

from src.models import Alert, StoredFile
from src.tasks import (
    _extract_file_metadata,
    _scan_file_for_threats,
    _send_file_alert,
    run_in_worker_loop,
)


@pytest.fixture(autouse=True)
def no_delay():
    with (
        patch("src.tasks.extract_file_metadata.delay") as ext,
        patch("src.tasks.send_file_alert.delay") as alert,
    ):
        yield ext, alert


class TestScanFileForThreats:
    async def test_clean_file(self, db_session, no_delay):
        f = StoredFile(
            id="clean1",
            title="clean",
            original_name="ok.txt",
            stored_name="clean1.txt",
            mime_type="text/plain",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("clean1")

        file_item = await db_session.get(StoredFile, "clean1")
        assert file_item.processing_status == "processing"
        assert file_item.scan_status == "clean"
        assert file_item.scan_details == "no threats found"
        assert file_item.requires_attention is False

    async def test_suspicious_extension(self, db_session, no_delay):
        f = StoredFile(
            id="exe1",
            title="bad",
            original_name="bad.exe",
            stored_name="exe1.exe",
            mime_type="application/x-msdownload",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("exe1")

        file_item = await db_session.get(StoredFile, "exe1")
        assert file_item.scan_status == "suspicious"
        assert "suspicious extension" in file_item.scan_details
        assert file_item.requires_attention is True

    async def test_large_file(self, db_session, no_delay):
        f = StoredFile(
            id="big1",
            title="large",
            original_name="big.txt",
            stored_name="big1.txt",
            mime_type="text/plain",
            size=11 * 1024 * 1024,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("big1")

        file_item = await db_session.get(StoredFile, "big1")
        assert file_item.scan_status == "suspicious"
        assert "larger than 10 MB" in file_item.scan_details

    async def test_pdf_mime_mismatch(self, db_session, no_delay):
        f = StoredFile(
            id="pdf1",
            title="fake pdf",
            original_name="doc.pdf",
            stored_name="pdf1.pdf",
            mime_type="image/png",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("pdf1")

        file_item = await db_session.get(StoredFile, "pdf1")
        assert file_item.scan_status == "suspicious"
        assert "pdf extension does not match mime type" in file_item.scan_details

    async def test_pdf_mime_allows_octet_stream(self, db_session, no_delay):
        f = StoredFile(
            id="pdf2",
            title="octet pdf",
            original_name="doc.pdf",
            stored_name="pdf2.pdf",
            mime_type="application/octet-stream",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("pdf2")

        file_item = await db_session.get(StoredFile, "pdf2")
        assert file_item.scan_status == "clean"

    async def test_missing_file(self, db_session, no_delay):
        await _scan_file_for_threats("does-not-exist")

    async def test_chains_to_extract_metadata(self, db_session, no_delay):
        ext_delay, _ = no_delay
        f = StoredFile(
            id="chain1",
            title="chain",
            original_name="c.txt",
            stored_name="chain1.txt",
            mime_type="text/plain",
            size=10,
        )
        db_session.add(f)
        await db_session.commit()

        await _scan_file_for_threats("chain1")
        ext_delay.assert_called_once_with("chain1")


class TestExtractFileMetadata:
    async def test_text_file(self, db_session, no_delay):
        ext_delay, alert_delay = no_delay
        f = StoredFile(
            id="text1",
            title="text",
            original_name="data.txt",
            stored_name="text1.txt",
            mime_type="text/plain",
            size=41,
        )
        db_session.add(f)
        await db_session.commit()

        (svc.STORAGE_DIR / "text1.txt").write_text(
            "hello world\nthis is a test file\nline three"
        )

        await _extract_file_metadata("text1")

        file_item = await db_session.get(StoredFile, "text1")
        assert file_item.processing_status == "processed"
        meta = file_item.metadata_json
        assert meta["extension"] == ".txt"
        assert meta["size_bytes"] == 41
        assert meta["mime_type"] == "text/plain"
        assert meta["line_count"] == 3
        assert meta["char_count"] == 42

    async def test_pdf_file(self, db_session, no_delay):
        pdf_content = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"2 0 obj\n<< /Type /Page >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page >>\nendobj\n"
            b"xref\n...\n%%EOF"
        )
        f = StoredFile(
            id="pdfmeta1",
            title="pdf",
            original_name="test.pdf",
            stored_name="pdfmeta1.pdf",
            mime_type="application/pdf",
            size=len(pdf_content),
        )
        db_session.add(f)
        await db_session.commit()

        (svc.STORAGE_DIR / "pdfmeta1.pdf").write_bytes(pdf_content)

        await _extract_file_metadata("pdfmeta1")

        file_item = await db_session.get(StoredFile, "pdfmeta1")
        assert file_item.processing_status == "processed"
        assert file_item.metadata_json["approx_page_count"] == 2
        assert file_item.metadata_json["mime_type"] == "application/pdf"

    async def test_stored_file_missing(self, db_session, no_delay):
        ext_delay, alert_delay = no_delay
        f = StoredFile(
            id="missing1",
            title="missing",
            original_name="missing.txt",
            stored_name="missing1.txt",
            mime_type="text/plain",
            size=10,
        )
        db_session.add(f)
        await db_session.commit()

        await _extract_file_metadata("missing1")

        file_item = await db_session.get(StoredFile, "missing1")
        assert file_item.processing_status == "failed"
        assert (
            file_item.scan_details == "stored file not found during metadata extraction"
        )
        alert_delay.assert_called_once_with("missing1")

    async def test_non_text_non_pdf(self, db_session, no_delay):
        f = StoredFile(
            id="bin1",
            title="binary",
            original_name="data.bin",
            stored_name="bin1.bin",
            mime_type="application/octet-stream",
            size=4,
        )
        db_session.add(f)
        await db_session.commit()

        (svc.STORAGE_DIR / "bin1.bin").write_bytes(b"\x00\x01\x02\x03")

        await _extract_file_metadata("bin1")

        file_item = await db_session.get(StoredFile, "bin1")
        assert file_item.processing_status == "processed"
        assert "line_count" not in file_item.metadata_json
        assert "approx_page_count" not in file_item.metadata_json

    async def test_missing_file_record(self, db_session, no_delay):
        await _extract_file_metadata("non-existent")


class TestSendFileAlert:
    async def test_info_alert(self, db_session, no_delay):
        f = StoredFile(
            id="info1",
            title="info",
            original_name="ok.txt",
            stored_name="info1.txt",
            mime_type="text/plain",
            size=1,
            processing_status="processed",
            requires_attention=False,
        )
        db_session.add(f)
        await db_session.commit()

        await _send_file_alert("info1")

        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 1
        assert alerts[0].level == "info"
        assert alerts[0].message == "File processed successfully"

    async def test_warning_alert(self, db_session, no_delay):
        f = StoredFile(
            id="warn1",
            title="warn",
            original_name="bad.txt",
            stored_name="warn1.txt",
            mime_type="text/plain",
            size=1,
            processing_status="processed",
            requires_attention=True,
            scan_details="suspicious extension .exe",
        )
        db_session.add(f)
        await db_session.commit()

        await _send_file_alert("warn1")

        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 1
        assert alerts[0].level == "warning"
        assert "requires attention" in alerts[0].message

    async def test_critical_alert(self, db_session, no_delay):
        f = StoredFile(
            id="crit1",
            title="crit",
            original_name="fail.txt",
            stored_name="crit1.txt",
            mime_type="text/plain",
            size=1,
            processing_status="failed",
            requires_attention=False,
        )
        db_session.add(f)
        await db_session.commit()

        await _send_file_alert("crit1")

        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 1
        assert alerts[0].level == "critical"
        assert alerts[0].message == "File processing failed"

    async def test_missing_file(self, db_session, no_delay):
        await _send_file_alert("non-existent")
        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 0


class TestRunInWorkerLoop:
    def test_runs_coroutine(self):
        async def sample():
            return 42

        result = run_in_worker_loop(sample())
        assert result == 42

    def test_reuses_event_loop(self):
        async def get_loop_id():
            import asyncio

            return id(asyncio.get_running_loop())

        first = run_in_worker_loop(get_loop_id())
        second = run_in_worker_loop(get_loop_id())
        assert first == second
