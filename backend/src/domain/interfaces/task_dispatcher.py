from abc import ABC, abstractmethod


class TaskDispatcher(ABC):
    @abstractmethod
    def dispatch_start_file_processing(
        self, file_id: str, pipeline_type: str = "default_file_processing"
    ) -> str:
        """Dispatch file processing task. Returns task id."""
