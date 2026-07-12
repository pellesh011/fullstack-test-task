from abc import ABC, abstractmethod

from src.domain.entities.scan_result import ScanResult
from src.domain.entities.stored_file import StoredFile


class ScanCheck(ABC):
    @property
    @abstractmethod
    def check_name(self) -> str: ...

    @abstractmethod
    def check(self, file: StoredFile) -> ScanResult | None: ...
