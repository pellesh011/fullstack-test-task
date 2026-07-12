from collections.abc import Sequence
from abc import ABC, abstractmethod

from src.domain.entities.stored_file import StoredFile
from src.domain.entities.alert import Alert
from src.domain.entities.scan_result import ScanResult


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

    @abstractmethod
    async def upsert_all(self, file_id: str, results: list[ScanResult]) -> None: ...
