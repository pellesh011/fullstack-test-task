import asyncio
import logging
from datetime import datetime
from typing import Any

from celery import Celery, chord, group
from celery.signals import worker_shutdown

from src.application.metadata.extractor_registry import extract_metadata
from src.core.config import settings
from src.domain.enums import (
    FileStatus,
    PipelineType,
    ProcessingTaskStatus,
    ProcessorType,
    TaskExecutionStatus,
)
from src.domain.entities.processing_task import ProcessingTask
from src.domain.entities.task_execution import TaskExecution
from src.domain.interfaces.file_storage import FileStorage
from src.infrastructure import DatabaseSessionManager
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.infrastructure.database.mappers.processing_task_mapper import (
    ProcessingTaskMapper,
)
from src.infrastructure.database.mappers.task_execution_mapper import (
    TaskExecutionMapper,
)
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.processing_task_repository import (
    SQLProcessingTaskRepository,
)
from src.infrastructure.repositories.task_execution_repository import (
    SQLTaskExecutionRepository,
)
from src.infrastructure.storage.local_file_storage import LocalFileStorage

logger = logging.getLogger(__name__)

celery_app = Celery(
    "file_tasks",
    broker=settings.resolved_redis_url,
    backend=settings.resolved_redis_url,
)

# Shared event loop for the worker process
_worker_loop: asyncio.AbstractEventLoop | None = None

_db = DatabaseSessionManager()
_storage: FileStorage = LocalFileStorage(settings.resolved_storage_dir)


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop


@worker_shutdown.connect
def _shutdown_worker_loop(**kwargs: Any) -> None:  # pyright: ignore[reportUnusedFunction]
    global _worker_loop
    if _worker_loop and not _worker_loop.is_closed():
        _worker_loop.close()
        _worker_loop = None


async def _save_task_execution(
    processing_task_id: int,
    processor: ProcessorType,
    status: TaskExecutionStatus,
    details: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
    execution_id: int | None = None,
) -> int:
    """Save or update a task execution record. Returns the execution id."""
    async with _db.session() as session:
        repo = SQLTaskExecutionRepository(session, TaskExecutionMapper())
        if execution_id is not None:
            existing = await repo.get_by_id(execution_id)
            if existing:
                existing.status = status
                existing.details = details
                existing.finished_at = finished_at
                existing.duration_ms = duration_ms
                saved = await repo.save(existing)
                assert saved.id is not None
                return saved.id
        execution = TaskExecution(
            processing_task_id=processing_task_id,
            processor=processor,
            status=status,
            details=details,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
        )
        saved = await repo.save(execution)
        assert saved.id is not None
        return saved.id


async def _update_processing_task_status(
    processing_task_id: int, status: ProcessingTaskStatus, error: str | None = None
) -> None:
    async with _db.session() as session:
        task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
        task = await task_repo.get_by_id(processing_task_id)
        if task:
            task.status = status
            if error:
                task.error = error
            if status == ProcessingTaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            if status in (ProcessingTaskStatus.SUCCESS, ProcessingTaskStatus.FAILED):
                task.finished_at = datetime.now()
            await task_repo.save(task)


async def _update_file_status(file_id: str, status: FileStatus) -> None:
    async with _db.session() as session:
        file_repo = SQLFileRepository(session, FileMapper())
        file_item = await file_repo.get_by_id(file_id)
        if file_item:
            file_item.status = status
            await file_repo.save(file_item)


@celery_app.task(bind=True)
def metadata_extract(self: Any, processing_task_id: int) -> dict[str, Any]:
    """Extract metadata from file."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                logger.warning("ProcessingTask %s not found", processing_task_id)
                return {}

            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(task.file_id)
            if not file_item:
                logger.warning("File %s not found", task.file_id)
                return {}

            await _update_processing_task_status(
                processing_task_id, ProcessingTaskStatus.RUNNING
            )

            started_at = datetime.now()
            execution_id = await _save_task_execution(
                processing_task_id=processing_task_id,
                processor=ProcessorType.METADATA_EXTRACTOR,
                status=TaskExecutionStatus.RUNNING,
                started_at=started_at,
            )

            try:
                if not await _storage.exists(file_item.stored_name):
                    finished_at = datetime.now()
                    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                    await _save_task_execution(
                        processing_task_id=processing_task_id,
                        processor=ProcessorType.METADATA_EXTRACTOR,
                        status=TaskExecutionStatus.FAILED,
                        details={
                            "error": "stored file not found during metadata extraction"
                        },
                        started_at=started_at,
                        finished_at=finished_at,
                        duration_ms=duration_ms,
                        execution_id=execution_id,
                    )
                    return {"status": "failed", "error": "File not found"}

                metadata = await extract_metadata(file_item, _storage)

                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)

                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.METADATA_EXTRACTOR,
                    status=TaskExecutionStatus.SUCCESS,
                    details=metadata,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )

                # Update file metadata
                file_item.metadata = metadata
                await file_repo.save(file_item)

                return {"status": "success", "metadata": metadata}

            except Exception as e:
                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                logger.exception("Metadata extraction failed")
                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.METADATA_EXTRACTOR,
                    status=TaskExecutionStatus.FAILED,
                    details={"error": str(e)},
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
                return {"status": "failed", "error": str(e)}

    return loop.run_until_complete(_run())


@celery_app.task(bind=True)
def size_check(self: Any, processing_task_id: int) -> dict[str, Any]:
    """Check file size."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                return {}

            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(task.file_id)
            if not file_item:
                return {}

            started_at = datetime.now()
            execution_id = await _save_task_execution(
                processing_task_id=processing_task_id,
                processor=ProcessorType.SIZE_CHECKER,
                status=TaskExecutionStatus.RUNNING,
                started_at=started_at,
            )

            try:
                max_size = settings.max_file_size_mb * 1024 * 1024
                actual_size = file_item.size
                message = None
                status = TaskExecutionStatus.SUCCESS

                if actual_size > max_size:
                    status = TaskExecutionStatus.WARNING
                    message = f"File size {actual_size} exceeds maximum allowed size {max_size}"

                details = {
                    "max_size": max_size,
                    "actual_size": actual_size,
                    "message": message,
                }

                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)

                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.SIZE_CHECKER,
                    status=status,
                    details=details,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )

                return {"status": "success", "details": details}

            except Exception as e:
                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                logger.exception("Size check failed")
                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.SIZE_CHECKER,
                    status=TaskExecutionStatus.FAILED,
                    details={"error": str(e)},
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
                return {"status": "failed", "error": str(e)}

    return loop.run_until_complete(_run())


@celery_app.task(bind=True)
def extension_validator(self: Any, processing_task_id: int) -> dict[str, Any]:
    """Validate file extension."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                return {}

            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(task.file_id)
            if not file_item:
                return {}

            started_at = datetime.now()
            execution_id = await _save_task_execution(
                processing_task_id=processing_task_id,
                processor=ProcessorType.EXTENSION_VALIDATOR,
                status=TaskExecutionStatus.RUNNING,
                started_at=started_at,
            )

            try:
                suspicious_extensions = settings.suspicious_extensions_parsed
                file_extension = file_item.original_name.split(".")[-1].lower()
                is_suspicious = f".{file_extension}" in suspicious_extensions

                details = {
                    "extension": file_extension,
                    "suspicious_extensions": suspicious_extensions,
                    "is_suspicious": is_suspicious,
                }

                status = (
                    TaskExecutionStatus.WARNING
                    if is_suspicious
                    else TaskExecutionStatus.SUCCESS
                )

                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)

                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.EXTENSION_VALIDATOR,
                    status=status,
                    details=details,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )

                return {"status": "success", "details": details}

            except Exception as e:
                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                logger.exception("Extension validation failed")
                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.EXTENSION_VALIDATOR,
                    status=TaskExecutionStatus.FAILED,
                    details={"error": str(e)},
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
                return {"status": "failed", "error": str(e)}

    return loop.run_until_complete(_run())


@celery_app.task(bind=True)
def mime_validate(self: Any, processing_task_id: int) -> dict[str, Any]:
    """Validate MIME type."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                return {}

            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(task.file_id)
            if not file_item:
                return {}

            started_at = datetime.now()
            execution_id = await _save_task_execution(
                processing_task_id=processing_task_id,
                processor=ProcessorType.MIME_VALIDATOR,
                status=TaskExecutionStatus.RUNNING,
                started_at=started_at,
            )

            try:
                is_mismatch = False
                message = None

                if (
                    file_item.original_mime_type
                    and file_item.original_mime_type != file_item.mime_type
                ):
                    is_mismatch = True
                    message = (
                        f"Client declared MIME type {file_item.original_mime_type} "
                        f"does not match detected type {file_item.mime_type}"
                    )

                details = {
                    "detected_mime": file_item.mime_type,
                    "original_mime": file_item.original_mime_type,
                    "is_mismatch": is_mismatch,
                    "message": message,
                }

                status = (
                    TaskExecutionStatus.WARNING
                    if is_mismatch
                    else TaskExecutionStatus.SUCCESS
                )

                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)

                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.MIME_VALIDATOR,
                    status=status,
                    details=details,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )

                return {"status": "success", "details": details}

            except Exception as e:
                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                logger.exception("MIME validation failed")
                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.MIME_VALIDATOR,
                    status=TaskExecutionStatus.FAILED,
                    details={"error": str(e)},
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
                return {"status": "failed", "error": str(e)}

    return loop.run_until_complete(_run())


@celery_app.task(bind=True)
def antivirus_scan(self: Any, processing_task_id: int) -> dict[str, Any]:
    """Scan file with antivirus."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                return {}

            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(task.file_id)
            if not file_item:
                return {}

            started_at = datetime.now()
            execution_id = await _save_task_execution(
                processing_task_id=processing_task_id,
                processor=ProcessorType.ANTIVIRUS_SCANNER,
                status=TaskExecutionStatus.RUNNING,
                started_at=started_at,
            )

            try:
                # Simulate antivirus scan - in production this would call clamav or similar
                details = {
                    "engine": "clamav",
                    "infected": False,
                    "threats": [],
                }

                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)

                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.ANTIVIRUS_SCANNER,
                    status=TaskExecutionStatus.SUCCESS,
                    details=details,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )

                return {"status": "success", "details": details}

            except Exception as e:
                finished_at = datetime.now()
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                logger.exception("Antivirus scan failed")
                await _save_task_execution(
                    processing_task_id=processing_task_id,
                    processor=ProcessorType.ANTIVIRUS_SCANNER,
                    status=TaskExecutionStatus.FAILED,
                    details={"error": str(e)},
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
                return {"status": "failed", "error": str(e)}

    return loop.run_until_complete(_run())


@celery_app.task(bind=True)
def finalize_processing(
    self: Any, results: list[dict[str, Any]], processing_task_id: int
) -> dict[str, Any]:
    """Finalize processing after all processors complete."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            task = await task_repo.get_by_id(processing_task_id)
            if not task:
                logger.warning("ProcessingTask %s not found", processing_task_id)
                return {}

            task_execution_repo = SQLTaskExecutionRepository(
                session, TaskExecutionMapper()
            )
            executions = await task_execution_repo.list_for_processing_task(
                processing_task_id
            )

            has_failed = any(e.status == TaskExecutionStatus.FAILED for e in executions)
            has_warning = any(
                e.status == TaskExecutionStatus.WARNING for e in executions
            )

            if has_failed:
                task_status = ProcessingTaskStatus.FAILED
                file_status = FileStatus.FAILED
            elif has_warning:
                task_status = ProcessingTaskStatus.SUCCESS
                file_status = FileStatus.WARNING
            else:
                task_status = ProcessingTaskStatus.SUCCESS
                file_status = FileStatus.OK

            await _update_processing_task_status(processing_task_id, task_status)
            await _update_file_status(task.file_id, file_status)

            return {
                "processing_task_status": task_status.value,
                "file_status": file_status.value,
                "executions_count": len(executions),
            }

    return loop.run_until_complete(_run())


def create_processing_workflow(
    processing_task_id: int,
    pipeline_type: PipelineType = PipelineType.DEFAULT_FILE_PROCESSING,
):
    """Create Celery workflow for file processing."""
    # Parallel processors
    parallel_processors = group(
        metadata_extract.s(processing_task_id),  # type: ignore[union-attr]
        size_check.s(processing_task_id),  # type: ignore[union-attr]
        extension_validator.s(processing_task_id),  # type: ignore[union-attr]
        mime_validate.s(processing_task_id),  # type: ignore[union-attr]
        antivirus_scan.s(processing_task_id),  # type: ignore[union-attr]
    )

    # Chain with finalize
    workflow = chord(parallel_processors)(finalize_processing.s(processing_task_id))  # type: ignore[union-attr]

    return workflow


@celery_app.task(bind=True)
def start_file_processing(
    self: Any, file_id: str, pipeline_type: str = "default_file_processing"
) -> dict[str, Any]:
    """Start file processing pipeline."""
    loop = _get_worker_loop()

    async def _run():
        async with _db.session() as session:
            file_repo = SQLFileRepository(session, FileMapper())
            file_item = await file_repo.get_by_id(file_id)
            if not file_item:
                logger.warning("File %s not found", file_id)
                return {"error": "File not found"}

            task_repo = SQLProcessingTaskRepository(session, ProcessingTaskMapper())
            processing_task = ProcessingTask(
                file_id=file_id,
                pipeline_type=PipelineType(pipeline_type),
                status=ProcessingTaskStatus.PENDING,
            )
            processing_task = await task_repo.save(processing_task)
            assert processing_task.id is not None

            # Update file status to processing
            await _update_file_status(file_id, FileStatus.PROCESSING)

            # Create and execute workflow
            result = create_processing_workflow(
                processing_task.id, PipelineType(pipeline_type)
            )

            return {
                "processing_task_id": processing_task.id,
                "workflow_id": result.id,
                "status": "started",
            }

    return loop.run_until_complete(_run())
