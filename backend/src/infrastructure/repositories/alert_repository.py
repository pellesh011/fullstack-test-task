from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.repositories import AlertRepository
from src.models import Alert


class SQLAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> Sequence[Alert]:
        result = await self._session.execute(
            select(Alert).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def save(self, alert: Alert) -> Alert:
        self._session.add(alert)
        await self._session.commit()
        await self._session.refresh(alert)
        return alert
