from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import FileRepository
from src.models import StoredFile


class SQLFileRepository(FileRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> Sequence[StoredFile]:
        result = await self._session.execute(
            select(StoredFile).order_by(StoredFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, file_id: str) -> StoredFile | None:
        return await self._session.get(StoredFile, file_id)

    async def save(self, file: StoredFile) -> StoredFile:
        self._session.add(file)
        await self._session.commit()
        await self._session.refresh(file)
        return file

    async def delete(self, file: StoredFile) -> None:
        await self._session.delete(file)
        await self._session.commit()
