from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.alert import Alert
from src.domain.interfaces.repositories import AlertRepository
from src.infrastructure.database.mappers.alert_mapper import AlertMapper
from src.infrastructure.database.models import Alert as AlertModel


class SQLAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession, mapper: AlertMapper):
        self._session = session
        self._mapper = mapper

    async def list_all(self) -> Sequence[Alert]:
        result = await self._session.execute(
            select(AlertModel).order_by(AlertModel.created_at.desc())
        )
        return [self._mapper.to_entity(item) for item in result.scalars().all()]

    async def save(self, alert: Alert) -> Alert:
        model = await self._session.merge(self._mapper.to_model(alert))
        await self._session.commit()
        await self._session.refresh(model)
        return self._mapper.to_entity(model)