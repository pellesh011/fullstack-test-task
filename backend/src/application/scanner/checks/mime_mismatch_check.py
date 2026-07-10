from pathlib import Path

from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


class MimeMismatchCheck(ScanCheck):
    def check(self, file: StoredFile) -> ScanResult | None:
        ext = Path(file.original_name).suffix.lower()
        if ext == ".pdf" and file.mime_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            return ScanResult(
                file_id=file.id,
                check_name="mime_mismatch",
                status="suspicious",
                message="pdf extension does not match mime type",
            )
        return None
