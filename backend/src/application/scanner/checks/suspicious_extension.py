from pathlib import Path

from src.core.config import settings
from src.domain.interfaces.scan_check import ScanCheck
from src.infrastructure.database.models import ScanResult, StoredFile


class SuspiciousExtensionCheck(ScanCheck):
    @property
    def check_name(self) -> str:
        return "suspicious_extension"

    def check(self, file: StoredFile) -> ScanResult | None:
        ext = Path(file.original_name).suffix.lower()
        if ext in settings.suspicious_extensions_parsed:
            return ScanResult(
                file_id=file.id,
                check_name="suspicious_extension",
                status="suspicious",
                message=f"suspicious extension {ext}",
            )
        return None
