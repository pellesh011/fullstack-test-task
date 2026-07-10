from unittest.mock import patch

import pytest
import src.tasks as tasks_mod
from sqlalchemy import select
from src.models import Alert, ScanResult, StoredFile


@pytest.fixture(autouse=True)
def no_delay():
    with (
        patch("src.tasks.extract_file_metadata.delay") as ext,
        patch("src.tasks.send_file_alert.delay") as alert,
    ):
        yield ext, alert


@pytest.fixture(autouse=True)
def _patch_task_deps(test_engine, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from src.infrastructure.database import DatabaseSessionManager
    from tests.conftest import TEST_STORAGE_DIR
    from src.infrastructure.storage.local_file_storage import LocalFileStorage

    manager = DatabaseSessionManager("sqlite+aiosqlite://")
    manager._engine = test_engine
    manager._session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    tasks_mod._db = manager
    tasks_mod._storage = LocalFileStorage(TEST_STORAGE_DIR)


@pytest.mark.asyncio
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

        await tasks_mod._scan_file_for_threats("clean1")

        file_item = await db_session.get(StoredFile, "clean1")
        assert file_item.processing_status == "processing"
        assert file_item.scan_status == "clean"
        assert file_item.requires_attention is False

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "clean1")
                )
            )
            .scalars()
            .all()
        )
        assert len(results) == 1
        assert results[0].check_name == "basic_scan"
        assert results[0].status == "clean"

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

        await tasks_mod._scan_file_for_threats("exe1")

        file_item = await db_session.get(StoredFile, "exe1")
        assert file_item.scan_status == "suspicious"
        assert file_item.requires_attention is True

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "exe1")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "suspicious_extension" for r in results)
        suspicious = next(r for r in results if r.check_name == "suspicious_extension")
        assert "suspicious extension" in suspicious.message

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

        await tasks_mod._scan_file_for_threats("big1")

        file_item = await db_session.get(StoredFile, "big1")
        assert file_item.scan_status == "suspicious"

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "big1")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "file_size" for r in results)

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

        await tasks_mod._scan_file_for_threats("pdf1")

        file_item = await db_session.get(StoredFile, "pdf1")
        assert file_item.scan_status == "suspicious"

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "pdf1")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "mime_mismatch" for r in results)

    async def test_mime_mismatch_exe_as_png(self, db_session, no_delay):
        f = StoredFile(
            id="exe2",
            title="fake exe",
            original_name="hack.exe",
            stored_name="exe2.exe",
            mime_type="image/png",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await tasks_mod._scan_file_for_threats("exe2")

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "exe2")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "mime_mismatch" for r in results)
        mismatch = next(r for r in results if r.check_name == "mime_mismatch")
        assert "exe" in mismatch.message
        assert "image/png" in mismatch.message

    async def test_mime_mismatch_zip_as_jpeg(self, db_session, no_delay):
        f = StoredFile(
            id="zip1",
            title="fake zip",
            original_name="archive.zip",
            stored_name="zip1.zip",
            mime_type="image/jpeg",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await tasks_mod._scan_file_for_threats("zip1")
        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "zip1")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "mime_mismatch" for r in results)

    async def test_mime_mismatch_client_declared_wrong(self, db_session, no_delay):
        f = StoredFile(
            id="client1",
            title="client mime mismatch",
            original_name="doc.pdf",
            stored_name="client1.pdf",
            mime_type="application/pdf",
            original_mime_type="text/plain",
            size=100,
        )
        db_session.add(f)
        await db_session.commit()

        await tasks_mod._scan_file_for_threats("client1")

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "client1")
                )
            )
            .scalars()
            .all()
        )
        assert any(r.check_name == "mime_mismatch" for r in results)
        mismatch = next(r for r in results if r.check_name == "mime_mismatch")
        assert "client declared" in mismatch.message
        assert "text/plain" in mismatch.message

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

        await tasks_mod._scan_file_for_threats("pdf2")

        file_item = await db_session.get(StoredFile, "pdf2")
        assert file_item.scan_status == "clean"

    async def test_missing_file(self, db_session, no_delay):
        await tasks_mod._scan_file_for_threats("does-not-exist")

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

        await tasks_mod._scan_file_for_threats("chain1")
        ext_delay.assert_called_once_with("chain1")


@pytest.mark.asyncio
class TestExtractFileMetadata:
    async def test_text_file(self, db_session, no_delay):
        from tests.conftest import TEST_STORAGE_DIR

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

        (TEST_STORAGE_DIR / "text1.txt").write_text(
            "hello world\nthis is a test file\nline three"
        )

        await tasks_mod._extract_file_metadata("text1")

        file_item = await db_session.get(StoredFile, "text1")
        assert file_item.processing_status == "processed"
        meta = file_item.metadata_json
        assert meta["extension"] == ".txt"
        assert meta["size_bytes"] == 41
        assert meta["mime_type"] == "text/plain"
        assert meta["line_count"] == 3
        assert meta["char_count"] == 42

    async def test_pdf_file(self, db_session, no_delay):
        from tests.conftest import TEST_STORAGE_DIR

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

        (TEST_STORAGE_DIR / "pdfmeta1.pdf").write_bytes(pdf_content)

        await tasks_mod._extract_file_metadata("pdfmeta1")

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

        await tasks_mod._extract_file_metadata("missing1")

        file_item = await db_session.get(StoredFile, "missing1")
        assert file_item.processing_status == "failed"

        results = (
            (
                await db_session.execute(
                    select(ScanResult).where(ScanResult.file_id == "missing1")
                )
            )
            .scalars()
            .all()
        )
        assert len(results) == 1
        assert results[0].check_name == "metadata_extraction"
        assert results[0].status == "error"
        assert "stored file not found" in results[0].message

        alert_delay.assert_called_once_with("missing1")

    async def test_non_text_non_pdf(self, db_session, no_delay):
        from tests.conftest import TEST_STORAGE_DIR

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

        (TEST_STORAGE_DIR / "bin1.bin").write_bytes(b"\x00\x01\x02\x03")

        await tasks_mod._extract_file_metadata("bin1")

        file_item = await db_session.get(StoredFile, "bin1")
        assert file_item.processing_status == "processed"
        assert "line_count" not in file_item.metadata_json
        assert "approx_page_count" not in file_item.metadata_json

    async def test_missing_file_record(self, db_session, no_delay):
        await tasks_mod._extract_file_metadata("non-existent")


@pytest.mark.asyncio
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

        await tasks_mod._send_file_alert("info1")

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
            scan_status="suspicious",
        )
        db_session.add(f)
        await db_session.commit()

        await tasks_mod._send_file_alert("warn1")

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

        await tasks_mod._send_file_alert("crit1")

        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 1
        assert alerts[0].level == "critical"
        assert alerts[0].message == "File processing failed"

    async def test_missing_file(self, db_session, no_delay):
        await tasks_mod._send_file_alert("non-existent")
        alerts = (await db_session.execute(select(Alert))).scalars().all()
        assert len(alerts) == 0


class TestRunAsync:
    def test_runs_coroutine(self):
        async def sample():
            return 42

        result = tasks_mod.run_async(sample())
        assert result == 42
