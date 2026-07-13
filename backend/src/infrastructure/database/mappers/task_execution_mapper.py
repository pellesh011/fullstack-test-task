from src.domain.entities.task_execution import TaskExecution
from src.infrastructure.database.models import TaskExecution as TaskExecutionModel

from .base import Mapper


class TaskExecutionMapper(Mapper[TaskExecution, TaskExecutionModel]):
    def to_entity(
        self,
        model: TaskExecutionModel,
    ) -> TaskExecution:
        return TaskExecution(
            id=model.id,
            processing_task_id=model.processing_task_id,
            processor=model.processor,
            status=model.status,
            details=model.details,
            started_at=model.started_at,
            finished_at=model.finished_at,
            duration_ms=model.duration_ms,
            created_at=model.created_at,
        )

    def to_model(
        self,
        entity: TaskExecution,
    ) -> TaskExecutionModel:
        return TaskExecutionModel(
            id=entity.id,
            processing_task_id=entity.processing_task_id,
            processor=entity.processor,
            status=entity.status,
            details=entity.details,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            duration_ms=entity.duration_ms,
        )
