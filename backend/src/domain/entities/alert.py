from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    id: int | None

    file_id: str

    level: AlertLevel

    message: str

    created_at: datetime | None = None
