from abc import ABC, abstractmethod

from src.models import ScanResult, StoredFile


class ScanCheck(ABC):
    @abstractmethod
    def check(self, file: StoredFile) -> ScanResult | None: ...
