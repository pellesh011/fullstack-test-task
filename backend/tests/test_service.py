from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from sqlalchemy import select
import src.service as svc

from src.models import StoredFile
from src.service import (
    create_alert,
    create_file,
    delete_file,
    get_file,
    get_file_path,
    list_alerts,
    list_files,
    update_file,
)


class TestListFiles:
    async def test_empty(self, db_session):
        result = await list_files()
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

        result = await list_files()
        assert len(result) == 1
        assert result[0].title == "test"

    async def test_ordered_by_created_at_desc(self, db_session):
        db_session.add(
            StoredFile(
                id="f2",
                title="second",
                original_name="b.txt",
                stored_name="f2.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        db_session.add(
            StoredFile(
                id="f1",
                title="first",
                original_name="a.txt",
                stored_name="f1.txt",
                mime_type="text/plain",
                size=1,
            )
        )
        await db_session.commit()

        result = await list_files()
        assert result[0].title == "second"
        assert result[1].title == "first"


class TestListAlerts:
    async def test_empty(self, db_session):
        result = await list_alerts()
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
        await create_alert("af1", "info", "test alert")

        result = await list_alerts()
        assert len(result) == 1
        assert result[0].level == "info"


class TestGetFile:
    async def test_existing(self, db_session):
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

        result = await get_file("gf1")
        assert result.id == "gf1"
        assert result.title == "found"

    async def test_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await get_file("nonexistent")
        assert exc.value.status_code == 404


class TestCreateFile:
    async def test_create_text_file(self, db_session):
        mock = MagicMock()
        mock.filename = "hello.txt"
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"hello world")

        result = await create_file("my file", mock)
        assert result.title == "my file"
        assert result.size == 11
        assert result.processing_status == "uploaded"

        stored_path = svc.STORAGE_DIR / result.stored_name
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"hello world"

    async def test_empty_file_raises(self):
        mock = MagicMock()
        mock.filename = "empty.txt"
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"")

        with pytest.raises(HTTPException) as exc:
            await create_file("empty", mock)
        assert exc.value.status_code == 400

    async def test_no_filename(self, db_session):
        mock = MagicMock()
        mock.filename = None
        mock.content_type = "text/plain"
        mock.read = AsyncMock(return_value=b"content")

        result = await create_file("no name", mock)
        assert result.original_name == result.stored_name

    async def test_no_content_type(self, db_session):
        mock = MagicMock()
        mock.filename = "file.txt"
        mock.content_type = None
        mock.read = AsyncMock(return_value=b"content")

        result = await create_file("no mime", mock)
        assert result.mime_type in ("text/plain", "application/octet-stream")


class TestUpdateFile:
    async def test_update_title(self, db_session):
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

        result = await update_file("uf1", "new title")
        assert result.title == "new title"

    async def test_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await update_file("nonexistent", "x")
        assert exc.value.status_code == 404


class TestDeleteFile:
    async def test_delete_existing(self, db_session):
        (svc.STORAGE_DIR / "df1.txt").write_text("data")
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

        await delete_file("df1")

        result = await db_session.execute(
            select(StoredFile).where(StoredFile.id == "df1")
        )
        assert result.scalar() is None
        assert not (svc.STORAGE_DIR / "df1.txt").exists()

    async def test_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await delete_file("nonexistent")
        assert exc.value.status_code == 404


class TestGetFilePath:
    async def test_existing(self, db_session):
        (svc.STORAGE_DIR / "gfp1.txt").write_text("data")
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

        item, path = await get_file_path("gfp1")
        assert item.id == "gfp1"
        assert path.exists()

    async def test_stored_file_missing(self, db_session):
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

        with pytest.raises(HTTPException) as exc:
            await get_file_path("gfp2")
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

        alert = await create_alert("ca1", "warning", "something")
        assert alert.file_id == "ca1"
        assert alert.level == "warning"
        assert alert.message == "something"
        assert alert.id is not None
