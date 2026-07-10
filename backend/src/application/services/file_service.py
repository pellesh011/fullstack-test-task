from uuid import uuid4
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
import mimetypes

from src.domain.interfaces.file_storage import FileStorage
from src.domain.interfaces.repositories import FileRepository
from src.models import StoredFile


class FileService:
    def __init__(self, file_repo: FileRepository, file_storage: FileStorage):
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
        content = await upload_file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty"
            )

        file_id = str(uuid4())
        suffix = Path(upload_file.filename or "").suffix
        stored_name = f"{file_id}{suffix}"

        self._file_storage.save(stored_name, content)

        file_item = StoredFile(
            id=file_id,
            title=title,
            original_name=upload_file.filename or stored_name,
            stored_name=stored_name,
            mime_type=upload_file.content_type
            or mimetypes.guess_type(stored_name)[0]
            or "application/octet-stream",
            size=len(content),
            processing_status="uploaded",
        )
        return await self._file_repo.save(file_item)

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
        self._file_storage.delete(file_item.stored_name)
        await self._file_repo.delete(file_item)

    def get_storage_path(self, file_item: StoredFile) -> Path:
        path = self._file_storage.get_path(file_item.stored_name)
        if not self._file_storage.exists(file_item.stored_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found"
            )
        return path
