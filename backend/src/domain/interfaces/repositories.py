from collections.abc import Sequence
from abc import ABC, abstractmethod

from src.models import Alert, ScanResult, StoredFile


class FileRepository(ABC):
    @abstractmethod
    async def list_all(self) -> Sequence[StoredFile]: ...

    @abstractmethod
    async def get_by_id(self, file_id: str) -> StoredFile | None: ...

    @abstractmethod
    async def save(self, file: StoredFile) -> StoredFile: ...

    @abstractmethod
    async def delete(self, file: StoredFile) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...


class AlertRepository(ABC):
    @abstractmethod
    async def list_all(self) -> Sequence[Alert]: ...

    @abstractmethod
    async def save(self, alert: Alert) -> Alert: ...


class ScanResultRepository(ABC):
    @abstractmethod
    async def list_for_file(self, file_id: str) -> Sequence[ScanResult]: ...

    @abstractmethod
    async def list_for_file_by_status(
        self, file_id: str, status: str
    ) -> Sequence[ScanResult]: ...

    @abstractmethod
    async def delete_for_file(self, file_id: str) -> None: ...

    @abstractmethod
    async def save_all(self, results: list[ScanResult]) -> None: ...
