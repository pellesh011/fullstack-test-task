from uuid import uuid4
from pathlib import Path
import logging

from fastapi import HTTPException, UploadFile, status
import magic

from src.core.config import settings
from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.repositories import FileRepository
from src.models import StoredFile
from src.tasks import scan_file_for_threats


logger = logging.getLogger(__name__)


class FileService:
    def __init__(
        self,
        file_repo: FileRepository,
        file_storage: FileStorage,
    ):
        self._file_repo = file_repo
        self._file_storage = file_storage

    async def list_files(self) -> list[StoredFile]:
        return list(await self._file_repo.list_all())

    async def get_file(self, file_id: str) -> StoredFile:
        file_item = await self._file_repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )
        return file_item

    async def create_file(self, title: str, upload_file: UploadFile) -> StoredFile:
        if (
            upload_file.size is not None
            and upload_file.size > settings.max_file_size_warning_mb * 1024 * 1024
        ):
            logger.warning(
                "File '%s' exceeds size warning limit: %d MB > %d MB",
                upload_file.filename,
                upload_file.size // (1024 * 1024),
                settings.max_file_size_warning_mb,
            )

        content = await upload_file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty"
            )

        file_id = str(uuid4())
        suffix = Path(upload_file.filename or "").suffix
        stored_name = f"{file_id}{suffix}"

        await self._file_storage.save(stored_name, content)

        try:
            detected_mime = magic.from_buffer(content, mime=True)
        except magic.MagicException:
            detected_mime = upload_file.content_type or "application/octet-stream"

        file_item = StoredFile(
            id=file_id,
            title=title,
            original_name=upload_file.filename or stored_name,
            stored_name=stored_name,
            mime_type=detected_mime,
            original_mime_type=upload_file.content_type,
            size=len(content),
            processing_status="uploaded",
        )
        try:
            saved = await self._file_repo.save(file_item)
            scan_file_for_threats.delay(saved.id)  # type: ignore[attr-defined]
        except Exception:
            await self._file_storage.delete(stored_name)
            raise

        return saved

    async def update_file(self, file_id: str, title: str) -> StoredFile:
        file_item = await self._file_repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )
        file_item.title = title
        return await self._file_repo.save(file_item)

    async def delete_file(self, file_id: str) -> None:
        file_item = await self._file_repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        await self._file_repo.delete(file_item)
        await self._file_repo.flush()

        try:
            await self._file_storage.delete(file_item.stored_name)
        except Exception:
            await self._file_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file from storage",
            )

        await self._file_repo.commit()

    def get_storage_path(self, file_item: StoredFile) -> Path:
        path = self._file_storage.get_path(file_item.stored_name)
        # Note: exists is now async, but this method is sync.
        # We check path existence directly since we already have the path.
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found"
            )
        return path
