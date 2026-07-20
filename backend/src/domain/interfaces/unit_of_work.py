from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional

from src.domain.interfaces.repositories import (
    FileRepository,
    ProcessingTaskRepository,
    TaskExecutionRepository,
)


class UnitOfWork(ABC):
    @property
    @abstractmethod
    def file_repo(self) -> FileRepository: ...

    @property
    @abstractmethod
    def processing_task_repo(self) -> ProcessingTaskRepository: ...

    @property
    @abstractmethod
    def task_execution_repo(self) -> TaskExecutionRepository: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...
