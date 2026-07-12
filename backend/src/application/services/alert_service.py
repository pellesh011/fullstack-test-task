from src.domain.enums import AlertLevel
from src.domain.interfaces.repositories import AlertRepository
from src.infrastructure.database.models import Alert


class AlertService:
    def __init__(self, alert_repo: AlertRepository):
        self._alert_repo = alert_repo

    async def list_alerts(self) -> list[Alert]:
        return list(await self._alert_repo.list_all())

    async def create_alert(
        self, file_id: str, level: AlertLevel, message: str
    ) -> Alert:
        alert = Alert(file_id=file_id, level=level.value, message=message)
        return await self._alert_repo.save(alert)

    async def create_alert_for_file(
        self,
        processing_status: str,
        requires_attention: bool,
        scan_status: str | None,
        file_id: str,
        scan_result_messages: list[str] | None = None,
    ) -> Alert:
        if processing_status == "failed":
            return await self.create_alert(
                file_id, AlertLevel.CRITICAL, "File processing failed"
            )
        if requires_attention:
            if scan_result_messages:
                details = "; ".join(scan_result_messages)
                message = f"File requires attention: {details}"
            else:
                message = f"File requires attention: status={scan_status}"
            return await self.create_alert(file_id, AlertLevel.WARNING, message)
        return await self.create_alert(
            file_id, AlertLevel.INFO, "File processed successfully"
        )
