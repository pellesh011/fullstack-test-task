from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import ScanResultRepository
from src.models import ScanResult


class SQLScanResultRepository(ScanResultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_file(self, file_id: str) -> Sequence[ScanResult]:
        result = await self._session.execute(
            select(ScanResult)
            .where(ScanResult.file_id == file_id)
            .order_by(ScanResult.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_file_by_status(
        self, file_id: str, status: str
    ) -> Sequence[ScanResult]:
        result = await self._session.execute(
            select(ScanResult)
            .where(ScanResult.file_id == file_id)
            .where(ScanResult.status == status)
            .order_by(ScanResult.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_for_file(self, file_id: str) -> None:
        await self._session.execute(
            delete(ScanResult).where(ScanResult.file_id == file_id)
        )

    async def save_all(self, results: list[ScanResult]) -> None:
        self._session.add_all(results)

    async def upsert_all(self, file_id: str, results: list[ScanResult]) -> None:
        if not results:
            return

        stmt = pg_insert(ScanResult).values(
            [
                {
                    "file_id": file_id,
                    "check_name": r.check_name,
                    "status": r.status,
                    "message": r.message,
                }
                for r in results
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["file_id", "check_name"],
            set_={
                "status": stmt.excluded.status,
                "message": stmt.excluded.message,
            },
        )
        await self._session.execute(stmt)
