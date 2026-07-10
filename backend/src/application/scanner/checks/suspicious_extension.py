from pathlib import Path

from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


class SuspiciousExtensionCheck(ScanCheck):
    SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}

    def check(self, file: StoredFile) -> ScanResult | None:
        ext = Path(file.original_name).suffix.lower()
        if ext in self.SUSPICIOUS_EXTENSIONS:
            return ScanResult(
                file_id=file.id,
                check_name="suspicious_extension",
                status="suspicious",
                message=f"suspicious extension {ext}",
            )
        return None
