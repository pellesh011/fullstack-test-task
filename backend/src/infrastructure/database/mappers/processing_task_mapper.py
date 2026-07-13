from src.domain.entities.processing_task import ProcessingTask
from src.infrastructure.database.models import ProcessingTask as ProcessingTaskModel

from .base import Mapper


class ProcessingTaskMapper(Mapper[ProcessingTask, ProcessingTaskModel]):
    def to_entity(
        self,
        model: ProcessingTaskModel,
    ) -> ProcessingTask:
        return ProcessingTask(
            id=model.id,
            file_id=model.file_id,
            pipeline_type=model.pipeline_type,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
            error=model.error,
            created_at=model.created_at,
        )

    def to_model(
        self,
        entity: ProcessingTask,
    ) -> ProcessingTaskModel:
        return ProcessingTaskModel(
            id=entity.id,
            file_id=entity.file_id,
            pipeline_type=entity.pipeline_type,
            status=entity.status,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            error=entity.error,
        )
