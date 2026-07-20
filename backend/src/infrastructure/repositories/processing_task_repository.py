from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.processing_task import ProcessingTask
from src.infrastructure.database.mappers.processing_task_mapper import (
    ProcessingTaskMapper,
)
from src.domain.interfaces.repositories import ProcessingTaskRepository
from src.infrastructure.database.models import ProcessingTask as ProcessingTaskModel


class SQLProcessingTaskRepository(ProcessingTaskRepository):
    def __init__(self, session: AsyncSession, mapper: ProcessingTaskMapper):
        self._session = session
        self._mapper = mapper

    async def get_by_id(self, task_id: int) -> ProcessingTask | None:
        item = await self._session.get(ProcessingTaskModel, task_id)
        return self._mapper.to_entity(item) if item else None

    async def get_latest_for_file(self, file_id: str) -> ProcessingTask | None:
        result = await self._session.execute(
            select(ProcessingTaskModel)
            .where(ProcessingTaskModel.file_id == file_id)
            .order_by(ProcessingTaskModel.created_at.desc())
            .limit(1)
        )
        item = result.scalar_one_or_none()
        return self._mapper.to_entity(item) if item else None

    async def save(self, task: ProcessingTask) -> ProcessingTask:
        item = await self._session.merge(self._mapper.to_model(task))
        await self._session.flush()
        await self._session.refresh(item)
        return self._mapper.to_entity(item)

    async def delete(self, task: ProcessingTask) -> None:
        item = await self._session.get(ProcessingTaskModel, task.id)
        if item:
            await self._session.delete(item)

    async def list_for_file(self, file_id: str) -> Sequence[ProcessingTask]:
        result = await self._session.execute(
            select(ProcessingTaskModel)
            .where(ProcessingTaskModel.file_id == file_id)
            .order_by(ProcessingTaskModel.created_at.desc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]
