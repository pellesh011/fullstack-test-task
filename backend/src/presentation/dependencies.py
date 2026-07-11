from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.metadata.extractor_registry import extract_metadata
from src.application.scanner.checks.file_size_check import FileSizeCheck
from src.application.scanner.checks.mime_mismatch_check import MimeMismatchCheck
from src.application.scanner.checks.suspicious_extension import (
    SuspiciousExtensionCheck,
)
from src.application.scanner.threat_scanner import ThreatScanner
from src.application.services.alert_service import AlertService
from src.application.services.file_service import FileService
from src.domain.interfaces.event_bus import EventBus
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.repositories import (
    AlertRepository,
    FileRepository,
    ScanResultRepository,
)
from src.infrastructure.database import DatabaseSessionManager
from src.infrastructure.event_bus.redis_event_bus import RedisEventBus
from src.infrastructure.repositories.alert_repository import SQLAlertRepository
from src.infrastructure.repositories.file_repository import SQLFileRepository
from src.infrastructure.repositories.scan_result_repository import (
    SQLScanResultRepository,
)
from src.infrastructure.storage.local_file_storage import LocalFileStorage
from src.core.config import settings

_manager = DatabaseSessionManager()
_storage: FileStorage = LocalFileStorage(settings.resolved_storage_dir)
_event_bus: EventBus = RedisEventBus(settings.resolved_redis_url)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _manager.session() as s:
        yield s


def get_file_repo(session: AsyncSession = Depends(get_session)) -> FileRepository:
    return SQLFileRepository(session)


def get_alert_repo(session: AsyncSession = Depends(get_session)) -> AlertRepository:
    return SQLAlertRepository(session)


def get_scan_result_repo(
    session: AsyncSession = Depends(get_session),
) -> ScanResultRepository:
    return SQLScanResultRepository(session)


def get_file_storage() -> FileStorage:
    return _storage


def get_event_bus() -> EventBus:
    return _event_bus


def get_file_service(
    file_repo: FileRepository = Depends(get_file_repo),
    file_storage: FileStorage = Depends(get_file_storage),
    event_bus: EventBus = Depends(get_event_bus),
) -> FileService:
    return FileService(
        file_repo=file_repo,
        file_storage=file_storage,
        event_bus=event_bus,
    )


def get_alert_service(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> AlertService:
    return AlertService(alert_repo=alert_repo)


def get_threat_scanner(
    scan_result_repo: ScanResultRepository = Depends(get_scan_result_repo),
) -> ThreatScanner:
    return ThreatScanner(
        checks=[
            SuspiciousExtensionCheck(),
            FileSizeCheck(),
            MimeMismatchCheck(),
        ],
        scan_result_repo=scan_result_repo,
    )
