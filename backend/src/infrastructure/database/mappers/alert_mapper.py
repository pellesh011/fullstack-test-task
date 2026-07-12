from src.domain.entities.alert import Alert
from src.infrastructure.database.models import Alert as AlertModel

from .base import Mapper


class AlertMapper(
    Mapper[Alert, AlertModel]
):

    def to_entity(
        self,
        model: AlertModel,
    ) -> Alert:

        return Alert(
            id=model.id,
            file_id=model.file_id,
            level=model.level,
            message=model.message,
            created_at=model.created_at
        )


    def to_model(
        self,
        entity: Alert,
    ) -> AlertModel:

        return AlertModel(
            id=entity.id,
            file_id=entity.file_id,
            level=entity.level,
            message=entity.message,
            created_at=entity.created_at
        )
