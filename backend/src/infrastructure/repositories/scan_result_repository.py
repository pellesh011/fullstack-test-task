from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.scan_result import ScanResult
from src.domain.interfaces.repositories import ScanResultRepository
from src.infrastructure.database.mappers.scan_result_mapper import ScanResultMapper
from src.infrastructure.database.models import ScanResult as ScanResultModel


class SQLScanResultRepository(ScanResultRepository):
    def __init__(self, session: AsyncSession, mapper: ScanResultMapper):
        self._session = session
        self._mapper = mapper

    async def list_for_file(self, file_id: str) -> Sequence[ScanResult]:
        result = await self._session.execute(
            select(ScanResultModel)
            .where(ScanResultModel.file_id == file_id)
            .order_by(ScanResultModel.created_at.desc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]

    async def list_for_file_by_status(
        self, file_id: str, status: str
    ) -> Sequence[ScanResult]:
        result = await self._session.execute(
            select(ScanResultModel)
            .where(ScanResultModel.file_id == file_id)
            .where(ScanResultModel.status == status)
            .order_by(ScanResultModel.created_at.desc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]

    async def delete_for_file(self, file_id: str) -> None:
        await self._session.execute(
            delete(ScanResultModel).where(ScanResultModel.file_id == file_id)
        )

    async def save_all(self, results: list[ScanResult]) -> None:
        models = [self._mapper.to_model(r) for r in results]
        self._session.add_all(models)

    async def upsert_all(self, file_id: str, results: list[ScanResult]) -> None:
        if not results:
            return

        # Delete existing results for this file and re-insert
        # (no unique constraint on file_id + check_name anymore)
        await self.delete_for_file(file_id)
        await self.save_all(results)