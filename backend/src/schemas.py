from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    original_mime_type: str | None = None
    size: int
    status: str
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    title: str


class TaskExecutionIssue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: str
    processor: str
    status: str
    details: dict[str, Any] | None = None
    created_at: datetime | None = None
