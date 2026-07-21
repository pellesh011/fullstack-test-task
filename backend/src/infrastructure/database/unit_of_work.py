from contextlib import asynccontextmanager
from types import TracebackType
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import (
    FileRepository,
    ProcessingTaskRepository,
    TaskExecutionRepository,
)
from src.domain.interfaces.unit_of_work import UnitOfWork
from src.infrastructure.database import DatabaseSessionManager
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.infrastructure.database.mappers.processing_task_mapper import (
    ProcessingTaskMapper,
)
from src.infrastructure.database.mappers.task_execution_mapper import (
    TaskExecutionMapper,
)
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.processing_task_repository import (
    SQLProcessingTaskRepository,
)
from src.infrastructure.repositories.task_execution_repository import (
    SQLTaskExecutionRepository,
)


class SQLUnitOfWork(UnitOfWork):
    def __init__(self, session_manager: DatabaseSessionManager):
        self._session_manager = session_manager
        self._session: AsyncSession | None = None
        self._file_repo: FileRepository | None = None
        self._processing_task_repo: ProcessingTaskRepository | None = None
        self._task_execution_repo: TaskExecutionRepository | None = None
        self._session_cm = None

    @property
    def file_repo(self) -> FileRepository:
        if self._file_repo is None:
            assert self._session is not None, (
                "Session not initialized. Use 'async with uow:'"
            )
            self._file_repo = SQLFileRepository(self._session, FileMapper())
        return self._file_repo

    @property
    def processing_task_repo(self) -> ProcessingTaskRepository:
        if self._processing_task_repo is None:
            assert self._session is not None, (
                "Session not initialized. Use 'async with uow:'"
            )
            self._processing_task_repo = SQLProcessingTaskRepository(
                self._session, ProcessingTaskMapper()
            )
        return self._processing_task_repo

    @property
    def task_execution_repo(self) -> TaskExecutionRepository:
        if self._task_execution_repo is None:
            assert self._session is not None, (
                "Session not initialized. Use 'async with uow:'"
            )
            self._task_execution_repo = SQLTaskExecutionRepository(
                self._session, TaskExecutionMapper()
            )
        return self._task_execution_repo

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()

    async def flush(self) -> None:
        if self._session:
            await self._session.flush()

    @asynccontextmanager
    async def _session_context(self):
        async with self._session_manager.session() as session:
            self._session = session
            try:
                yield session
            finally:
                self._session = None
                self._file_repo = None
                self._processing_task_repo = None
                self._task_execution_repo = None

    async def __aenter__(self) -> "SQLUnitOfWork":
        self._session_cm = self._session_context()
        await self._session_cm.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if self._session_cm:
            return await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
        return None
