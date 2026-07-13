from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.enums import ProcessorType, TaskExecutionStatus


@dataclass
class TaskExecution:
    id: int | None = None
    processing_task_id: int = 0
    processor: ProcessorType = ProcessorType.METADATA_EXTRACTOR
    status: TaskExecutionStatus = TaskExecutionStatus.PENDING
    details: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    created_at: datetime | None = None

    def __post_init__(self):
        if type(self.processor) is str:
            self.processor = ProcessorType(self.processor)
        if type(self.status) is str:
            self.status = TaskExecutionStatus(self.status)
