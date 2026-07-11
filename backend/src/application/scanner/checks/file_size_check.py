from src.core.config import settings
from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


class FileSizeCheck(ScanCheck):
    def check(self, file: StoredFile) -> ScanResult | None:
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if file.size > max_bytes:
            return ScanResult(
                file_id=file.id,
                check_name="file_size",
                status="suspicious",
                message=f"file is larger than {settings.max_file_size_mb} MB",
            )
        return None
