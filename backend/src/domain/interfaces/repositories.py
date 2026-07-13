from collections.abc import Sequence
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from src.domain.entities.file import File
from src.domain.entities.processing_task import ProcessingTask
from src.domain.entities.task_execution import TaskExecution


class FileRepository(ABC):
    @abstractmethod
    async def list_all(self) -> Sequence[File]: ...

    @abstractmethod
    async def get_by_id(self, file_id: str) -> File | None: ...

    @abstractmethod
    async def save(self, file: File) -> File: ...

    @abstractmethod
    async def delete(self, file: File) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...


class ProcessingTaskRepository(ABC):
    @abstractmethod
    async def get_by_id(self, task_id: int) -> ProcessingTask | None: ...

    @abstractmethod
    async def get_latest_for_file(self, file_id: str) -> ProcessingTask | None: ...

    @abstractmethod
    async def save(self, task: ProcessingTask) -> ProcessingTask: ...

    @abstractmethod
    async def delete(self, task: ProcessingTask) -> None: ...

    @abstractmethod
    async def list_for_file(self, file_id: str) -> Sequence[ProcessingTask]: ...


class TaskExecutionIssue:
    def __init__(
        self,
        id: int,
        file_id: str,
        processor: str,
        status: str,
        details: dict[str, Any] | None,
        created_at: datetime | None,
    ):
        self.id = id
        self.file_id = file_id
        self.processor = processor
        self.status = status
        self.details = details
        self.created_at = created_at


class TaskExecutionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, execution_id: int) -> TaskExecution | None: ...

    @abstractmethod
    async def list_for_processing_task(
        self, processing_task_id: int
    ) -> Sequence[TaskExecution]: ...

    @abstractmethod
    async def list_non_success(self) -> Sequence[TaskExecutionIssue]: ...

    @abstractmethod
    async def save(self, execution: TaskExecution) -> TaskExecution: ...

    @abstractmethod
    async def save_all(self, executions: list[TaskExecution]) -> None: ...
