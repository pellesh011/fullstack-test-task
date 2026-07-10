from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from src.application.services.alert_service import AlertService
from src.application.services.file_service import FileService
from src.infrastructure.repositories.alert_repository import SQLAlertRepository
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.scan_result_repository import (
    SQLScanResultRepository,
)
from src.infrastructure.storage.local_file_storage import LocalFileStorage
from src.models import ScanResult, StoredFile

pytestmark = pytest.mark.asyncio


class TestListFiles:
    async def test_empty(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
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

        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
    )
        result = await svc.list_files()
        assert len(result) == 1
        assert result[0].title == "test"

    async def test_ordered_by_created_at_desc(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
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
        svc = AlertService(alert_repo=SQLAlertRepository(db_session))
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

        alert_repo = SQLAlertRepository(db_session)
        svc = AlertService(alert_repo=alert_repo)
        await svc.create_alert("af1", "info", "test alert")

        result = await svc.list_alerts()
        assert len(result) == 1
        assert result[0].level == "info"


class TestGetFile:
    async def test_existing(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
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
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
    )
        with pytest.raises(HTTPException) as exc:
            await svc.get_file("nonexistent")
        assert exc.value.status_code == 404


class TestCreateFile:
    async def test_create_text_file(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=LocalFileStorage(TEST_STORAGE_DIR),
        event_bus=AsyncMock(),
    )
        mock = MagicMock()
        mock.filename = "hello.txt"
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"hello world")

        result = await svc.create_file("my file", mock)
        assert result.title == "my file"
        assert result.size == 11
        assert result.processing_status == "uploaded"

        stored_path = TEST_STORAGE_DIR / result.stored_name
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"hello world"

    async def test_empty_file_raises(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
    )
        mock = MagicMock()
        mock.filename = "empty.txt"
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"")

        with pytest.raises(HTTPException) as exc:
            await svc.create_file("empty", mock)
        assert exc.value.status_code == 400

    async def test_no_filename(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=LocalFileStorage(TEST_STORAGE_DIR),
        event_bus=AsyncMock(),
    )
        mock = MagicMock()
        mock.filename = None
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"content")

        result = await svc.create_file("no name", mock)
        assert result.original_name == result.stored_name

    async def test_no_content_type(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=LocalFileStorage(TEST_STORAGE_DIR),
        event_bus=AsyncMock(),
    )
        mock = MagicMock()
        mock.filename = "file.txt"
        mock.content_type = None
        mock.read = AsyncMock(return_value=b"content")

        result = await svc.create_file("no mime", mock)
        assert result.mime_type in ("text/plain", "application/octet-stream")


class TestUpdateFile:
    async def test_update_title(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
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
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
    )
        with pytest.raises(HTTPException) as exc:
            await svc.update_file("nonexistent", "x")
        assert exc.value.status_code == 404


class TestDeleteFile:
    async def test_delete_existing(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=storage,
        event_bus=AsyncMock(),
    )
        storage.save("df1.txt", b"data")
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
        assert not storage.exists("df1.txt")

    async def test_not_found(self, db_session):
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=MagicMock(),
        event_bus=AsyncMock(),
    )
        with pytest.raises(HTTPException) as exc:
            await svc.delete_file("nonexistent")
        assert exc.value.status_code == 404

    async def test_rollback_on_storage_failure(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=storage,
        event_bus=AsyncMock(),
    )
        storage.save("df2.txt", b"data")
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

        with patch.object(storage, "delete", side_effect=OSError("Storage unavailable")):
            with pytest.raises(HTTPException) as exc:
                await svc.delete_file("df2")
            assert exc.value.status_code == 500

        result = await db_session.execute(
            select(StoredFile).where(StoredFile.id == "df2")
        )
        assert result.scalar() is not None
        assert storage.exists("df2.txt")

        storage.delete("df2.txt")


class TestGetStoragePath:
    async def test_existing(self, db_session):
        from tests.conftest import TEST_STORAGE_DIR

        storage = LocalFileStorage(TEST_STORAGE_DIR)
        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=storage,
        event_bus=AsyncMock(),
    )
        storage.save("gfp1.txt", b"data")
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

        svc = FileService(
            file_repo=SQLFileRepository(db_session),
        file_storage=LocalFileStorage(TEST_STORAGE_DIR),
        event_bus=AsyncMock(),
    )
        db_session.add(
            StoredFile(
                id="gfp2",
                title="x",
                original_name="f.txt",
                stored_name="gfp2.txt",
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

        svc = AlertService(alert_repo=SQLAlertRepository(db_session))
        alert = await svc.create_alert("ca1", "warning", "something")
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

        repo = SQLScanResultRepository(db_session)
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

        repo = SQLScanResultRepository(db_session)
        result = await repo.list_for_file("sr1")
        assert len(result) == 1
        assert result[0].check_name == "basic_scan"
        assert result[0].status == "clean"


class TestCreateAlertForFile:
    async def test_info_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session))
        alert = await svc.create_alert_for_file(
            processing_status="processed",
            requires_attention=False,
            scan_status="clean",
            file_id="f1",
        )
        assert alert.level == "info"
        assert alert.message == "File processed successfully"

    async def test_warning_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session))
        alert = await svc.create_alert_for_file(
            processing_status="processed",
            requires_attention=True,
            scan_status="suspicious",
            file_id="f1",
        )
        assert alert.level == "warning"
        assert "requires attention" in alert.message

    async def test_critical_alert(self, db_session):
        svc = AlertService(alert_repo=SQLAlertRepository(db_session))
        alert = await svc.create_alert_for_file(
            processing_status="failed",
            requires_attention=False,
            scan_status=None,
            file_id="f1",
        )
        assert alert.level == "critical"
        assert alert.message == "File processing failed"
