from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import PipelineType, ProcessingTaskStatus


@dataclass
class ProcessingTask:
    id: int | None = None
    file_id: str = ""
    pipeline_type: PipelineType = PipelineType.DEFAULT_FILE_PROCESSING
    status: ProcessingTaskStatus = ProcessingTaskStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    created_at: datetime | None = None

    def __post_init__(self):
        if type(self.status) is str:
            self.status = ProcessingTaskStatus(self.status)
        if type(self.pipeline_type) is str:
            self.pipeline_type = PipelineType(self.pipeline_type)
