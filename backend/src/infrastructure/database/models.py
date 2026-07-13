from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.domain.enums import (
    FileStatus,
    PipelineType,
    ProcessingTaskStatus,
    ProcessorType,
    TaskExecutionStatus,
)


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    original_mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus, native_enum=False),
        nullable=False,
        default=FileStatus.NEW,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        "ProcessingTask",
        back_populates="file",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("ix_files_status", "status"),
        Index("ix_files_created_at", "created_at"),
    )


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_type: Mapped[PipelineType] = mapped_column(
        SQLEnum(PipelineType, native_enum=False), nullable=False
    )
    status: Mapped[ProcessingTaskStatus] = mapped_column(
        SQLEnum(ProcessingTaskStatus, native_enum=False),
        nullable=False,
        default=ProcessingTaskStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    file: Mapped["File"] = relationship("File", back_populates="processing_tasks")
    task_executions: Mapped[list["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="processing_task",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("ix_processing_tasks_file_id", "file_id"),
        Index("ix_processing_tasks_status", "status"),
        Index("ix_processing_tasks_pipeline_type", "pipeline_type"),
    )


class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processing_task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processing_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    processor: Mapped[ProcessorType] = mapped_column(
        SQLEnum(ProcessorType, native_enum=False), nullable=False
    )
    status: Mapped[TaskExecutionStatus] = mapped_column(
        SQLEnum(TaskExecutionStatus, native_enum=False),
        nullable=False,
        default=TaskExecutionStatus.PENDING,
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    processing_task: Mapped["ProcessingTask"] = relationship(
        "ProcessingTask", back_populates="task_executions"
    )

    __table_args__ = (
        Index("ix_task_executions_processing_task_id", "processing_task_id"),
        Index("ix_task_executions_processor", "processor"),
        Index("ix_task_executions_status", "status"),
    )
