from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.stored_file import StoredFile
from src.infrastructure.database.mappers.file_mapper import FileMapper
from src.domain.interfaces.repositories import FileRepository
from src.infrastructure.database.models import StoredFile as StoredFilemodel


class SQLFileRepository(FileRepository):
    def __init__(self, session: AsyncSession, mapper: FileMapper):
        self._session = session
        self._mapper = mapper

    async def list_all(self) -> Sequence[StoredFile]:
        result = await self._session.execute(
            select(StoredFilemodel).order_by(StoredFilemodel.created_at.desc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]

    async def get_by_id(self, file_id: str) -> StoredFile | None:
        item = await self._session.get(StoredFilemodel, file_id)
        return self._mapper.to_entity(item) if item else None

    async def save(self, file: StoredFile) -> StoredFile:
        item = await self._session.merge(self._mapper.to_model(file))
        await self._session.commit()
        await self._session.refresh(item)
        return self._mapper.to_entity(item)

    async def delete(self, file: StoredFile) -> None:
        item = await self._session.get(StoredFilemodel, file.id)
        if item:
            await self._session.delete(item)

    async def flush(self) -> None:
        await self._session.flush()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def commit(self) -> None:
        await self._session.commit()