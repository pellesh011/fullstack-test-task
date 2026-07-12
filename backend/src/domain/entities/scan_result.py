from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ScanResultStatus(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    ERROR = "error"


@dataclass
class ScanResult:
    file_id: str

    check_name: str

    status: ScanResultStatus

    message: str | None = None

    created_at: datetime | None = None

    id: int | None = None

    def is_failed(self) -> bool:
        return self.status in {
            ScanResultStatus.SUSPICIOUS,
            ScanResultStatus.ERROR,
        }
