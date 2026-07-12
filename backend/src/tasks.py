import asyncio
import logging
from typing import Any
from celery import Celery
from celery.signals import worker_shutdown

from src.application.metadata.extractor_registry import extract_metadata
from src.application.scanner.checks.file_size_check import FileSizeCheck
from src.application.scanner.checks.mime_mismatch_check import MimeMismatchCheck
from src.application.scanner.checks.suspicious_extension import (
    SuspiciousExtensionCheck,
)
from src.application.scanner.threat_scanner import ThreatScanner
from src.application.services.alert_service import AlertService
from src.core.config import settings
from src.domain.interfaces.file_storage import FileStorage
from src.infrastructure import DatabaseSessionManager
from src.domain.entities.scan_result import ScanResult, ScanResultStatus
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.infrastructure.database.mappers.alert_mapper import AlertMapper
from src.infrastructure.database.mappers.scan_result_mapper import ScanResultMapper
from src.infrastructure.repositories.alert_repository import SQLAlertRepository
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.scan_result_repository import (
    SQLScanResultRepository,
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


async def _scan_file_for_threats(file_id: str) -> None:
    async with _db.session() as session:
        file_repo = SQLFileRepository(session, FileMapper())
        scan_result_repo = SQLScanResultRepository(session, ScanResultMapper())

        file_item = await file_repo.get_by_id(file_id)
        if not file_item:
            logger.warning("File %s not found for scanning", file_id)
            return

        file_item.processing_status = "processing"

        scanner = ThreatScanner(
            checks=[
                SuspiciousExtensionCheck(),
                FileSizeCheck(),
                MimeMismatchCheck(),
            ],
            scan_result_repo=scan_result_repo,
        )

        _, scan_status, has_suspicious = await scanner.scan(file_item)

        file_item.scan_status = scan_status
        file_item.requires_attention = has_suspicious
        await file_repo.save(file_item)
        await session.commit()

    extract_file_metadata.delay(file_id)  # type: ignore[attr-defined]


async def _extract_file_metadata(file_id: str) -> None:
    async with _db.session() as session:
        file_repo = SQLFileRepository(session, FileMapper())
        scan_result_repo = SQLScanResultRepository(session, ScanResultMapper())

        file_item = await file_repo.get_by_id(file_id)
        if not file_item:
            logger.warning("File %s not found for metadata extraction", file_id)
            return

        if not await _storage.exists(file_item.stored_name):
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            scan_result = ScanResult(
                file_id=file_id,
                check_name="metadata_extraction",
                status=ScanResultStatus.ERROR,
                message="stored file not found during metadata extraction",
            )
            await scan_result_repo.save_all([scan_result])
            await file_repo.save(file_item)
            await session.commit()
            send_file_alert.delay(file_id)  # type: ignore[attr-defined]
            return

        metadata = await extract_metadata(file_item, _storage)

        file_item.metadata = metadata
        file_item.processing_status = "processed"
        await file_repo.save(file_item)
        await session.commit()

    send_file_alert.delay(file_id)  # type: ignore[attr-defined]


async def _send_file_alert(file_id: str) -> None:
    async with _db.session() as session:
        file_repo = SQLFileRepository(session, FileMapper())
        alert_repo = SQLAlertRepository(session, AlertMapper())
        scan_result_repo = SQLScanResultRepository(session, ScanResultMapper())

        file_item = await file_repo.get_by_id(file_id)
        if not file_item:
            logger.warning("File %s not found for alert creation", file_id)
            return

        scan_results = await scan_result_repo.list_for_file_by_status(
            file_id, "suspicious"
        )
        error_results = await scan_result_repo.list_for_file_by_status(file_id, "error")
        suspicious_messages = [sr.message for sr in scan_results if sr.message]
        error_messages = [sr.message for sr in error_results if sr.message]
        all_messages = suspicious_messages + error_messages

        alert_service = AlertService(alert_repo=alert_repo)
        await alert_service.create_alert_for_file(
            processing_status=file_item.processing_status,
            requires_attention=file_item.requires_attention,
            scan_status=file_item.scan_status,
            file_id=file_id,
            scan_result_messages=all_messages,
        )


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    loop = _get_worker_loop()
    loop.run_until_complete(_scan_file_for_threats(file_id))


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    loop = _get_worker_loop()
    loop.run_until_complete(_extract_file_metadata(file_id))


@celery_app.task
def send_file_alert(file_id: str) -> None:
    loop = _get_worker_loop()
    loop.run_until_complete(_send_file_alert(file_id))
