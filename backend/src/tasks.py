import asyncio
import os
from pathlib import Path
from celery import Celery
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.models import Alert, ScanResult, StoredFile
from src.service import STORAGE_DIR, get_db_url

REDIS_URL = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")
_worker_loop: asyncio.AbstractEventLoop | None = None


def run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


celery_app = Celery("file_tasks", broker=REDIS_URL, backend=REDIS_URL)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_db_url())
    return _engine


_session_maker = None


def get_session_maker():
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_maker


async def _scan_file_for_threats(file_id: str) -> None:
    async with get_session_maker()() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        file_item.processing_status = "processing"

        checks: list[ScanResult] = []
        extension = Path(file_item.original_name).suffix.lower()

        if extension in {".exe", ".bat", ".cmd", ".sh", ".js"}:
            checks.append(
                ScanResult(
                    file_id=file_id,
                    check_name="suspicious_extension",
                    status="suspicious",
                    message=f"suspicious extension {extension}",
                )
            )

        if file_item.size > 10 * 1024 * 1024:
            checks.append(
                ScanResult(
                    file_id=file_id,
                    check_name="file_size",
                    status="suspicious",
                    message="file is larger than 10 MB",
                )
            )

        if extension == ".pdf" and file_item.mime_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            checks.append(
                ScanResult(
                    file_id=file_id,
                    check_name="mime_mismatch",
                    status="suspicious",
                    message="pdf extension does not match mime type",
                )
            )

        has_suspicious = any(c.status == "suspicious" for c in checks)

        if not checks:
            checks.append(
                ScanResult(
                    file_id=file_id,
                    check_name="basic_scan",
                    status="clean",
                    message="no threats found",
                )
            )

        await session.execute(delete(ScanResult).where(ScanResult.file_id == file_id))
        session.add_all(checks)
        file_item.scan_status = "suspicious" if has_suspicious else "clean"
        file_item.requires_attention = has_suspicious
        await session.commit()

    extract_file_metadata.delay(file_id)


async def _extract_file_metadata(file_id: str) -> None:
    async with get_session_maker()() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        stored_path = STORAGE_DIR / file_item.stored_name
        if not stored_path.exists():
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            result = ScanResult(
                file_id=file_id,
                check_name="metadata_extraction",
                status="error",
                message="stored file not found during metadata extraction",
            )
            session.add(result)
            await session.commit()
            send_file_alert.delay(file_id)
            return

        metadata = {
            "extension": Path(file_item.original_name).suffix.lower(),
            "size_bytes": file_item.size,
            "mime_type": file_item.mime_type,
        }

        if file_item.mime_type.startswith("text/"):
            content = stored_path.read_text(encoding="utf-8", errors="ignore")
            metadata["line_count"] = len(content.splitlines())
            metadata["char_count"] = len(content)
        elif file_item.mime_type == "application/pdf":
            content = stored_path.read_bytes()
            metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

        file_item.metadata_json = metadata
        file_item.processing_status = "processed"
        await session.commit()

    send_file_alert.delay(file_id)


async def _send_file_alert(file_id: str) -> None:
    async with get_session_maker()() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        if file_item.processing_status == "failed":
            alert = Alert(
                file_id=file_id, level="critical", message="File processing failed"
            )
        elif file_item.requires_attention:
            alert = Alert(
                file_id=file_id,
                level="warning",
                message=f"File requires attention: status={file_item.scan_status}",
            )
        else:
            alert = Alert(
                file_id=file_id, level="info", message="File processed successfully"
            )

        session.add(alert)
        await session.commit()


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(_send_file_alert(file_id))
