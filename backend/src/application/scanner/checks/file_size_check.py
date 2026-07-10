from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


class FileSizeCheck(ScanCheck):
    MAX_SIZE = 10 * 1024 * 1024

    def check(self, file: StoredFile) -> ScanResult | None:
        if file.size > self.MAX_SIZE:
            return ScanResult(
                file_id=file.id,
                check_name="file_size",
                status="suspicious",
                message="file is larger than 10 MB",
            )
        return None
