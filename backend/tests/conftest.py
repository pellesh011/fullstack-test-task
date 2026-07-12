import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.app import app
from src.infrastructure.database.models import Base

TEST_STORAGE_DIR = Path(tempfile.mkdtemp())


@pytest.fixture(autouse=True)
def _mock_celery_tasks(monkeypatch):
    monkeypatch.setattr("src.tasks.scan_file_for_threats.delay", lambda file_id: None)
    monkeypatch.setattr("src.tasks.extract_file_metadata.delay", lambda file_id: None)
    monkeypatch.setattr("src.tasks.send_file_alert.delay", lambda file_id: None)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _patch_dependencies(test_engine, monkeypatch):
    from src.presentation import dependencies as deps
    from src.infrastructure.database import DatabaseSessionManager

    manager = DatabaseSessionManager("sqlite+aiosqlite://")
    manager._engine = test_engine
    manager._session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    deps._manager = manager

    from src.infrastructure.storage.local_file_storage import LocalFileStorage

    deps._storage = LocalFileStorage(TEST_STORAGE_DIR)


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))

    maker = async_sessionmaker(test_engine, expire_on_commit=True)
    async with maker() as s:
        yield s


@pytest_asyncio.fixture
async def client(test_engine):
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def upload_file(client: AsyncClient) -> dict:
    content = b"hello world\nthis is a test file\nline three"
    response = await client.post(
        "/files",
        data={"title": "test file"},
        files={"file": ("test.txt", content, "text/plain")},
    )
    return response.json()
