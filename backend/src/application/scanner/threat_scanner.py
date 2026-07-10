from src.domain.interfaces.repositories import ScanResultRepository
from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


class ThreatScanner:
    def __init__(
        self,
        checks: list[ScanCheck],
        scan_result_repo: ScanResultRepository,
    ):
        self._checks = checks
        self._scan_result_repo = scan_result_repo

    async def scan(self, file: StoredFile) -> tuple[list[ScanResult], str, bool]:
        results: list[ScanResult] = []
        for check in self._checks:
            result = check.check(file)
            if result is not None:
                results.append(result)

        has_suspicious = any(r.status == "suspicious" for r in results)

        if not results:
            results.append(
                ScanResult(
                    file_id=file.id,
                    check_name="basic_scan",
                    status="clean",
                    message="no threats found",
                )
            )

        await self._scan_result_repo.delete_for_file(file.id)
        await self._scan_result_repo.save_all(results)

        scan_status = "suspicious" if has_suspicious else "clean"
        return results, scan_status, has_suspicious
