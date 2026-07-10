from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings


class DatabaseSessionManager:
    def __init__(self, database_url: str | None = None):
        self._database_url = database_url or settings.database_url
        self._engine = None
        self._session_maker = None

    def _ensure(self) -> None:
        if self._engine is not None:
            return
        self._engine = create_async_engine(self._database_url)
        self._session_maker = async_sessionmaker(self._engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        self._ensure()
        async with self._session_maker() as s:  # type: ignore
            yield s

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
