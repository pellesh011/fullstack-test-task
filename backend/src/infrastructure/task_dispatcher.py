from src.domain.interfaces.task_dispatcher import TaskDispatcher


class CeleryTaskDispatcher(TaskDispatcher):
    def dispatch_start_file_processing(
        self, file_id: str, pipeline_type: str = "default_file_processing"
    ) -> str:
        from src.tasks import start_file_processing

        result = start_file_processing.delay(file_id, pipeline_type)  # type: ignore[union-attr]
        return result.id or ""
