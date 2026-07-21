from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.application.services.file_service import FileService
from src.domain.enums import FileStatus
from src.domain.exceptions import FileEmptyError
from src.domain.interfaces.task_dispatcher import TaskDispatcher
from src.infrastructure.storage.local_file_storage import LocalFileStorage


class FakeUploadFile:
    """Mimics FastAPI UploadFile for testing."""

    def __init__(
        self,
        content: bytes,
        filename: str = "test.txt",
        content_type: str = "text/plain",
    ):
        self._content = content
        self._pos = 0
        self.filename = filename
        self.content_type = content_type
        self.size = len(content)

    @property
    def file(self):
        return self

    def seek(self, pos: int):
        self._pos = pos

    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            chunk = self._content[self._pos :]
            self._pos = len(self._content)
        else:
            chunk = self._content[self._pos : self._pos + size]
            self._pos += len(chunk)
        return chunk


class MockTaskDispatcher(TaskDispatcher):
    def __init__(self):
        self.dispatched: list[str] = []

    def dispatch_start_file_processing(
        self, file_id: str, pipeline_type: str = "default_file_processing"
    ) -> str:
        self.dispatched.append(file_id)
        return "mock-task-id"


@dataclass
class FakeUnitOfWork:
    file_repo: AsyncMock
    task: MockTaskDispatcher

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def flush(self):
        pass


@pytest_asyncio.fixture
async def storage(tmp_path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path)


@pytest_asyncio.fixture
def mock_uow():
    repo = AsyncMock()
    repo.save.side_effect = lambda obj: obj
    return FakeUnitOfWork(file_repo=repo, task=MockTaskDispatcher())


@pytest_asyncio.fixture
def task_dispatcher():
    return MockTaskDispatcher()


class TestCreateFileStreaming:
    async def test_create_file_streams_content(
        self, storage: LocalFileStorage, mock_uow
    ):
        service = FileService(mock_uow, storage, mock_uow.task)
        upload = FakeUploadFile(b"hello world content")

        result = await service.create_file("my file", upload)

        assert result.title == "my file"
        assert result.size == 19
        assert result.status == FileStatus.NEW
        assert result.mime_type == "text/plain"

        content = await storage.read_bytes(result.stored_name)
        assert content == b"hello world content"

    async def test_create_file_empty_raises(self, storage: LocalFileStorage, mock_uow):
        service = FileService(mock_uow, storage, mock_uow.task)
        upload = FakeUploadFile(b"")

        with pytest.raises(FileEmptyError):
            await service.create_file("empty", upload)

    async def test_create_file_large_content(self, storage: LocalFileStorage, mock_uow):
        service = FileService(mock_uow, storage, mock_uow.task)
        large_content = b"X" * 50000
        upload = FakeUploadFile(large_content, filename="large.bin")

        result = await service.create_file("large file", upload)

        assert result.size == 50000
        content = await storage.read_bytes(result.stored_name)
        assert content == large_content

    async def test_create_file_mime_detected_from_content(
        self, storage: LocalFileStorage, mock_uow
    ):
        service = FileService(mock_uow, storage, mock_uow.task)
        # PDF magic bytes - reliably detected by python-magic
        pdf_header = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        upload = FakeUploadFile(
            pdf_header, filename="fake.txt", content_type="text/plain"
        )

        result = await service.create_file("pdf file", upload)

        assert result.mime_type == "application/pdf"
        assert result.original_mime_type == "text/plain"

    async def test_create_file_dispatches_processing(
        self, storage: LocalFileStorage, mock_uow
    ):
        service = FileService(mock_uow, storage, mock_uow.task)
        upload = FakeUploadFile(b"content")

        result = await service.create_file("dispatched", upload)

        assert result.id in mock_uow.task.dispatched

    async def test_create_file_saves_to_database(
        self, storage: LocalFileStorage, mock_uow
    ):
        service = FileService(mock_uow, storage, mock_uow.task)
        upload = FakeUploadFile(b"db content")

        await service.create_file("db file", upload)

        mock_uow.file_repo.save.assert_called_once()
        saved_file = mock_uow.file_repo.save.call_args[0][0]
        assert saved_file.title == "db file"
        assert saved_file.original_name == "test.txt"

    async def test_create_file_deletes_storage_on_db_error(
        self, storage: LocalFileStorage
    ):
        repo = AsyncMock()
        repo.save.side_effect = RuntimeError("DB error")
        uow = FakeUnitOfWork(file_repo=repo, task=MockTaskDispatcher())
        service = FileService(uow, storage, uow.task)
        upload = FakeUploadFile(b"content")

        with pytest.raises(RuntimeError):
            await service.create_file("will fail", upload)

        assert len(list(storage._storage_dir.iterdir())) == 0
