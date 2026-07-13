from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.enums import FileStatus


@dataclass
class File:
    id: str
    title: str
    original_name: str
    stored_name: str
    mime_type: str
    size: int
    status: FileStatus = FileStatus.NEW
    original_mime_type: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
