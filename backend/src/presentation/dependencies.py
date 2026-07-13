from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.file_service import FileService
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.repositories import FileRepository, TaskExecutionRepository
from src.domain.interfaces.task_dispatcher import TaskDispatcher
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.infrastructure.database.mappers.task_execution_mapper import (
    TaskExecutionMapper,
)
from src.infrastructure.database import DatabaseSessionManager
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.task_execution_repository import (
    SQLTaskExecutionRepository,
)
from src.infrastructure.storage.local_file_storage import LocalFileStorage
from src.infrastructure.task_dispatcher import CeleryTaskDispatcher
from src.core.config import settings

_manager = DatabaseSessionManager()
_storage: FileStorage = LocalFileStorage(settings.resolved_storage_dir)
_task_dispatcher: TaskDispatcher = CeleryTaskDispatcher()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _manager.session() as s:
        yield s


def get_file_repo(session: AsyncSession = Depends(get_session)) -> FileRepository:
    return SQLFileRepository(session, FileMapper())


def get_file_storage() -> FileStorage:
    return _storage


def get_task_dispatcher() -> TaskDispatcher:
    return _task_dispatcher


def get_file_service(
    file_repo: FileRepository = Depends(get_file_repo),
    file_storage: FileStorage = Depends(get_file_storage),
    task_dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
) -> FileService:
    return FileService(
        file_repo=file_repo,
        file_storage=file_storage,
        task_dispatcher=task_dispatcher,
    )


def get_task_execution_repo(
    session: AsyncSession = Depends(get_session),
) -> TaskExecutionRepository:
    return SQLTaskExecutionRepository(session, TaskExecutionMapper())
