from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.task_execution import TaskExecution
from src.domain.interfaces.repositories import TaskExecutionIssue
from src.infrastructure.database.mappers.task_execution_mapper import (
    TaskExecutionMapper,
)
from src.domain.interfaces.repositories import TaskExecutionRepository
from src.infrastructure.database.models import TaskExecution as TaskExecutionModel
from src.infrastructure.database.models import ProcessingTask as ProcessingTaskModel


class SQLTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self, session: AsyncSession, mapper: TaskExecutionMapper):
        self._session = session
        self._mapper = mapper

    async def get_by_id(self, execution_id: int) -> TaskExecution | None:
        item = await self._session.get(TaskExecutionModel, execution_id)
        return self._mapper.to_entity(item) if item else None

    async def save(self, execution: TaskExecution) -> TaskExecution:
        item = await self._session.merge(self._mapper.to_model(execution))
        await self._session.flush()
        await self._session.refresh(item)
        return self._mapper.to_entity(item)

    async def list_for_processing_task(
        self, processing_task_id: int
    ) -> Sequence[TaskExecution]:
        result = await self._session.execute(
            select(TaskExecutionModel)
            .where(TaskExecutionModel.processing_task_id == processing_task_id)
            .order_by(TaskExecutionModel.created_at.asc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]

    async def save_all(self, executions: list[TaskExecution]) -> None:
        models = [self._mapper.to_model(e) for e in executions]
        self._session.add_all(models)
        await self._session.flush()

    async def list_non_success(self) -> Sequence[TaskExecutionIssue]:
        result = await self._session.execute(
            select(TaskExecutionModel, ProcessingTaskModel.file_id)
            .join(
                ProcessingTaskModel,
                TaskExecutionModel.processing_task_id == ProcessingTaskModel.id,
            )
            .where(TaskExecutionModel.status != "success")
            .order_by(TaskExecutionModel.created_at.desc())
        )
        return [
            TaskExecutionIssue(
                id=row[0].id,
                file_id=row[1],
                processor=row[0].processor.value,
                status=row[0].status.value,
                details=row[0].details,
                created_at=row[0].created_at,
            )
            for row in result.all()
        ]

    async def update_status(
        self, execution_id: int, status: str, details: dict[str, Any] | None = None
    ) -> TaskExecution | None:
        from src.domain.enums import TaskExecutionStatus

        item = await self._session.get(TaskExecutionModel, execution_id)
        if item:
            item.status = TaskExecutionStatus(status)
            if details is not None:
                item.details = details
            await self._session.flush()
            await self._session.refresh(item)
            return self._mapper.to_entity(item)
        return None
