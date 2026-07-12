from src.core.config import settings
from src.domain.entities.scan_result import ScanResult, ScanResultStatus
from src.domain.entities.stored_file import StoredFile
from src.domain.interfaces.scan_check import ScanCheck


class FileSizeCheck(ScanCheck):
    @property
    def check_name(self) -> str:
        return "file_size"

    def check(self, file: StoredFile) -> ScanResult | None:
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if file.size > max_bytes:
            return ScanResult(
                file_id=file.id,
                check_name="file_size",
                status=ScanResultStatus.SUSPICIOUS,
                message=f"file is larger than {settings.max_file_size_mb} MB",
            )
        return None
