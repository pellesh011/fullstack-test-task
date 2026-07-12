from src.domain.entities.scan_result import ScanResult
from src.infrastructure.database.models import ScanResult as ScanResultModel

from .base import Mapper


class ScanResultMapper(Mapper[ScanResult, ScanResultModel]):
    def to_entity(
        self,
        model: ScanResultModel,
    ) -> ScanResult:

        return ScanResult(
            id=model.id,
            file_id=model.file_id,
            check_name=model.check_name,
            status=model.status,
            message=model.message,
            created_at=model.created_at,
        )

    def to_model(
        self,
        entity: ScanResult,
    ) -> ScanResultModel:

        return ScanResultModel(
            id=entity.id,
            file_id=entity.file_id,
            check_name=entity.check_name,
            status=entity.status,
            message=entity.message,
            created_at=entity.created_at,
        )
