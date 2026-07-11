import logging
from src.domain.interfaces.repositories import ScanResultRepository
from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile


logger = logging.getLogger(__name__)


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
            try:
                result = check.check(file)
                if result is not None:
                    # Use check_name from the check class
                    if hasattr(check, 'check_name'):
                        result.check_name = check.check_name
                    results.append(result)
            except Exception as e:
                logger.exception("Scan check %s failed for file %s", check.__class__.__name__, file.id)
                results.append(
                    ScanResult(
                        file_id=file.id,
                        check_name=getattr(check, 'check_name', check.__class__.__name__.lower().replace("check", "")),
                        status="error",
                        message=f"Check failed: {e}",
                    )
                )

        has_suspicious = any(r.status == "suspicious" for r in results)

        # Upsert instead of delete + insert to avoid N+1
        await self._scan_result_repo.upsert_all(file.id, results)

        scan_status = "suspicious" if has_suspicious else "clean"
        return results, scan_status, has_suspicious