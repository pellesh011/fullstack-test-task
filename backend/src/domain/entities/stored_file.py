from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanStatus(StrEnum):
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"


@dataclass
class StoredFile:
    id: str
    title: str
    original_name: str
    stored_name: str

    mime_type: str
    size: int

    original_mime_type: str | None = None

    processing_status: str = ProcessingStatus.UPLOADED
    scan_status: str | None = None

    metadata: dict | None = None
    metadata_json: dict | None = None

    requires_attention: bool = False

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if self.metadata_json is not None:
            self.metadata = self.metadata_json
        elif self.metadata is not None:
            self.metadata_json = self.metadata