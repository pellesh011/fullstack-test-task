from abc import ABC, abstractmethod

from src.infrastructure.database.models import ScanResult, StoredFile


class ScanCheck(ABC):
    @property
    @abstractmethod
    def check_name(self) -> str: ...

    @abstractmethod
    def check(self, file: StoredFile) -> ScanResult | None: ...
