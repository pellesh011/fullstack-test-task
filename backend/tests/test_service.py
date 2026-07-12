from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from src.application.services.alert_service import AlertService
from src.application.services.file_service import FileService
from src.domain.enums import AlertLevel
from src.infrastructure.repositories.alert_repository import SQLAlertRepository
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.scan_result_repository import (
    SQLScanResultRepository,
)
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.infrastructure.database.mappers.alert_mapper import AlertMapper
from src.infrastructure.database.mappers.scan_result_mapper import ScanResultMapper
from src.infrastructure.storage.local_file_storage import LocalFileStorage
from src.infrastructure.database.models import ScanResult, StoredFile

pytestmark = pytest.mark.asyncio


def make_async_storage(**overrides) -> AsyncMock:
    """Create an AsyncMock for LocalFileStorage with all methods async."""
    storage = AsyncMock(spec=LocalFileStorage)
    storage.save = AsyncMock(return_value=None)
    storage.get_path = AsyncMock(return_value="/tmp/test.txt")
    storage.exists = AsyncMock(return_value=True)
    storage.delete = AsyncMock(return_value=True)
    storage.read_bytes = AsyncMock(return_value=b"")
    storage.read_text = AsyncMock(return_value="")
    for k, v in overrides.items():
        setattr(storage, k, v)
    return storage


class TestListFiles:
    async def test_empty(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/f1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        result = await svc.list_files()
        assert result == []

    async def test_with_files(self, db_session):
        db_session.add(
            StoredFile(
                id="f1",
                title="test",
                original_name="t.txt",
                stored_name="f1.txt",
                mime_type="text/plain",
                size=10,
            )
        )
        await db_session.commit()

        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/f1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        result = await svc.list_files()
        assert len(result) == 1
        assert result[0].title == "test"

    async def test_ordered_by_created_at_desc(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/f1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        db_session.add_all(
            [
                StoredFile(
                    id="f2",
                    title="second",
                    original_name="b.txt",
                    stored_name="f2.txt",
                    mime_type="text/plain",
                    size=1,
                ),
                StoredFile(
                    id="f1",
                    title="first",
                    original_name="a.txt",
                    stored_name="f1.txt",
                    mime_type="text/plain",
                    size=1,
                ),
            ]
        )
        await db_session.commit()

        result = await svc.list_files()
        assert result[0].title == "second"
        assert result[1].title == "first"


class TestListAlerts:
    async def test_empty(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        result = await svc.list_alerts()
        assert result == []

    async def test_with_alerts(self, db_session):
        db_session.add(
            StoredFile(
                id="af1",
                title="t",
                original_name="t.txt",
                stored_name="af1.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        await db_session.commit()

        alert_repo = SQLAlertRepository(db_session, AlertMapper())
        svc = AlertService(alert_repo=alert_repo)
        await svc.create_alert("af1", AlertLevel.INFO, "test alert")

        result = await svc.list_alerts()
        assert len(result) == 1
        assert result[0].level == "info"


class TestGetFile:
    async def test_existing(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/gf1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        db_session.add(
            StoredFile(
                id="gf1",
                title="found",
                original_name="f.txt",
                stored_name="gf1.txt",
                mime_type="text/plain",
                size=10,
            )
        )
        await db_session.commit()

        result = await svc.get_file("gf1")
        assert result.id == "gf1"
        assert result.title == "found"

    async def test_not_found(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/gf1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        with pytest.raises(HTTPException) as exc:
            await svc.get_file("nonexistent")
        assert exc.value.status_code == 404


class TestCreateFile:
    async def test_create_text_file(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        mock = MagicMock()
        mock.filename = "hello.txt"
        mock.content_type = "text/plain"
        mock.size = 11
        mock.read = AsyncMock(return_value=b"hello world")

        result = await svc.create_file("my file", mock)
        assert result.title == "my file"
        assert result.size == 11
        assert result.processing_status == "uploaded"

        assert await storage.exists(result.stored_name)
        assert (await storage.read_bytes(result.stored_name)) == b"hello world"

    async def test_empty_file_raises(self, db_session):
        storage = make_async_storage()

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        mock = MagicMock()
        mock.filename = "empty.txt"
        mock.content_type = "text/plain"
        mock.size = 0
        mock.read = AsyncMock(return_value=b"")

        with pytest.raises(HTTPException) as exc:
            await svc.create_file("empty", mock)
        assert exc.value.status_code == 400

    async def test_no_filename(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        mock = MagicMock()
        mock.filename = None
        mock.content_type = "text/plain"
        mock.size = 7
        mock.read = AsyncMock(return_value=b"content")

        result = await svc.create_file("no name", mock)
        assert result.original_name == result.stored_name

    async def test_no_content_type(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        mock = MagicMock()
        mock.filename = "file.txt"
        mock.content_type = None
        mock.size = 7
        mock.read = AsyncMock(return_value=b"content")

        result = await svc.create_file("no mime", mock)
        assert result.mime_type in ("text/plain", "application/octet-stream")


class TestUpdateFile:
    async def test_update_title(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/uf1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        db_session.add(
            StoredFile(
                id="uf1",
                title="old",
                original_name="f.txt",
                stored_name="uf1.txt",
                mime_type="text/plain",
                size=10,
            )
        )
        await db_session.commit()

        result = await svc.update_file("uf1", "new title")
        assert result.title == "new title"

    async def test_not_found(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/uf1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        with pytest.raises(HTTPException) as exc:
            await svc.update_file("nonexistent", "x")
        assert exc.value.status_code == 404


class TestDeleteFile:
    async def test_delete_existing(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        await storage.save("df1.txt", b"data")
        db_session.add(
            StoredFile(
                id="df1",
                title="x",
                original_name="f.txt",
                stored_name="df1.txt",
                mime_type="text/plain",
                size=4,
            )
        )
        await db_session.commit()

        await svc.delete_file("df1")

        result = await db_session.execute(
            select(StoredFile).where(StoredFile.id == "df1")
        )
        assert result.scalar() is None
        assert not await storage.exists("df1.txt")

    async def test_not_found(self, db_session):
        storage = make_async_storage()
        storage.get_path = AsyncMock(return_value="/tmp/df1.txt")

        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        with pytest.raises(HTTPException) as exc:
            await svc.delete_file("nonexistent")
        assert exc.value.status_code == 404

    async def test_rollback_on_storage_failure(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        await storage.save("df2.txt", b"data")
        db_session.add(
            StoredFile(
                id="df2",
                title="x",
                original_name="f.txt",
                stored_name="df2.txt",
                mime_type="text/plain",
                size=4,
            )
        )
        await db_session.commit()

        with patch.object(storage, "delete", AsyncMock(side_effect=OSError("Storage unavailable"))):
            with pytest.raises(HTTPException) as exc:
                await svc.delete_file("df2")
            assert exc.value.status_code == 500

        result = await db_session.execute(
            select(StoredFile).where(StoredFile.id == "df2")
        )
        assert result.scalar() is not None
        assert await storage.exists("df2.txt")

        await storage.delete("df2.txt")


class TestGetStoragePath:
    async def test_existing(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        await storage.save("gfp1.txt", b"data")
        db_session.add(
            StoredFile(
                id="gfp1",
                title="x",
                original_name="f.txt",
                stored_name="gfp1.txt",
                mime_type="text/plain",
                size=4,
            )
        )
        await db_session.commit()

        file_item = await svc.get_file("gfp1")
        path = svc.get_storage_path(file_item)
        assert path.exists()

    async def test_stored_file_missing(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session, FileMapper()),
            file_storage=storage,
        )
        db_session.add(
            StoredFile(
                id="gfp2",
                title="x",
                original_name="f.txt",
                stored_name="gfp2_missing.txt",
                mime_type="text/plain",
                size=4,
            )
        )
        await db_session.commit()

        file_item = await svc.get_file("gfp2")
        with pytest.raises(HTTPException) as exc:
            svc.get_storage_path(file_item)
        assert exc.value.status_code == 404


class TestCreateAlert:
    async def test_creates_alert(self, db_session):
        db_session.add(
            StoredFile(
                id="ca1",
                title="t",
                original_name="t.txt",
                stored_name="ca1.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        await db_session.commit()

        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        alert = await svc.create_alert("ca1", AlertLevel.WARNING, "something")
        assert alert.file_id == "ca1"
        assert alert.level == "warning"
        assert alert.message == "something"
        assert alert.id is not None


class TestListScanResults:
    async def test_empty(self, db_session):
        db_session.add(
            StoredFile(
                id="sr_empty",
                title="t",
                original_name="t.txt",
                stored_name="sr_empty.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        await db_session.commit()

        repo = SQLScanResultRepository(db_session, ScanResultMapper())
        result = await repo.list_for_file("sr_empty")
        assert result == []

    async def test_with_results(self, db_session):
        db_session.add(
            StoredFile(
                id="sr1",
                title="t",
                original_name="t.txt",
                stored_name="sr1.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        await db_session.commit()

        db_session.add(
            ScanResult(file_id="sr1", check_name="basic_scan", status="clean")
        )
        await db_session.commit()

        repo = SQLScanResultRepository(db_session, ScanResultMapper())
        result = await repo.list_for_file("sr1")
        assert len(result) == 1
        assert result[0].check_name == "basic_scan"
        assert result[0].status == "clean"


class TestCreateAlertForFile:
    async def test_info_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        alert = await svc.create_alert_for_file(
            processing_status="processed",
            requires_attention=False,
            scan_status="clean",
            file_id="f1",
        )
        assert alert.level == "info"
        assert alert.message == "File processed successfully"

    async def test_warning_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        alert = await svc.create_alert_for_file(
            processing_status="processed",
            requires_attention=True,
            scan_status="suspicious",
            file_id="f1",
        )
        assert alert.level == "warning"
        assert "requires attention" in alert.message

    async def test_warning_alert_with_scan_messages(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        alert = await svc.create_alert_for_file(
            processing_status="processed",
            requires_attention=True,
            scan_status="suspicious",
            file_id="f1",
            scan_result_messages=["suspicious extension .exe", "file is larger than 10 MB"],
        )
        assert alert.level == "warning"
        assert alert.message == "File requires attention: suspicious extension .exe; file is larger than 10 MB"

    async def test_critical_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session, AlertMapper()))
        alert = await svc.create_alert_for_file(
            processing_status="failed",
            requires_attention=False,
            scan_status=None,
            file_id="f1",
        )
        assert alert.level == "critical"
        assert alert.message == "File processing failed"