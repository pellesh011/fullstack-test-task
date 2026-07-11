from pathlib import Path

from src.domain.interfaces.scan_check import ScanCheck
from src.models import ScanResult, StoredFile

KNOWN_MIME_TYPES: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".svg": {"image/svg+xml"},
    ".ico": {"image/x-icon", "image/vnd.microsoft.icon"},
    ".bmp": {"image/bmp"},
    ".tiff": {"image/tiff"},
    ".tif": {"image/tiff"},
    ".avif": {"image/avif"},
    ".txt": {"text/plain"},
    ".html": {"text/html"},
    ".htm": {"text/html"},
    ".css": {"text/css"},
    ".csv": {"text/csv"},
    ".json": {"application/json"},
    ".xml": {"application/xml", "text/xml"},
    ".yaml": {"text/yaml", "application/x-yaml"},
    ".yml": {"text/yaml", "application/x-yaml"},
    ".md": {"text/markdown"},
    ".zip": {"application/zip"},
    ".gz": {"application/gzip"},
    ".tar": {"application/x-tar"},
    ".bz2": {"application/x-bzip2"},
    ".7z": {"application/x-7z-compressed"},
    ".rar": {"application/vnd.rar"},
    ".mp3": {"audio/mpeg"},
    ".wav": {"audio/wav"},
    ".ogg": {"audio/ogg", "video/ogg"},
    ".flac": {"audio/flac"},
    ".aac": {"audio/aac"},
    ".mp4": {"video/mp4"},
    ".avi": {"video/x-msvideo"},
    ".mkv": {"video/x-matroska"},
    ".mov": {"video/quicktime"},
    ".wmv": {"video/x-ms-wmv"},
    ".flv": {"video/x-flv"},
    ".doc": {"application/msword"},
    ".dot": {"application/msword"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".ppt": {"application/vnd.ms-powerpoint"},
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    },
    ".odt": {"application/vnd.oasis.opendocument.text"},
    ".ods": {"application/vnd.oasis.opendocument.spreadsheet"},
    ".odp": {"application/vnd.oasis.opendocument.presentation"},
    ".exe": {
        "application/x-msdownload",
        "application/vnd.microsoft.portable-executable",
    },
    ".dll": {"application/x-msdownload"},
    ".bat": {"text/plain", "application/x-bat"},
    ".cmd": {"text/plain"},
    ".com": {"application/x-msdownload"},
    ".msi": {"application/x-msi"},
    ".sh": {"text/plain", "application/x-sh"},
    ".bash": {"text/plain", "application/x-sh"},
    ".pl": {"text/plain", "text/x-perl"},
    ".py": {"text/plain", "text/x-python"},
    ".rb": {"text/plain", "text/x-ruby"},
    ".ps1": {"text/plain"},
    ".vbs": {"text/plain"},
    ".js": {"text/javascript", "application/javascript"},
    ".jsx": {"text/javascript", "application/javascript"},
    ".ts": {"text/typescript", "application/typescript"},
    ".tsx": {"text/typescript", "application/typescript"},
    ".wasm": {"application/wasm"},
    ".epub": {"application/epub+zip"},
    ".apk": {"application/vnd.android.package-archive"},
    ".deb": {"application/x-debian-package"},
    ".rpm": {"application/x-rpm"},
    ".iso": {"application/x-iso9660-image"},
    ".ttf": {"font/ttf"},
    ".otf": {"font/otf"},
    ".woff": {"font/woff"},
    ".woff2": {"font/woff2"},
}


class MimeMismatchCheck(ScanCheck):
    @property
    def check_name(self) -> str:
        return "mime_mismatch"

    def check(self, file: StoredFile) -> ScanResult | None:
        issues: list[str] = []

        ext = Path(file.original_name).suffix.lower()
        if ext:
            expected = KNOWN_MIME_TYPES.get(ext)
            if (
                expected is not None
                and file.mime_type not in expected
                and file.mime_type != "application/octet-stream"
            ):
                issues.append(
                    f"extension '{ext}' does not match mime type '{file.mime_type}' "
                    f"(expected one of: {', '.join(sorted(expected))})"
                )

        if (
            file.original_mime_type
            and file.original_mime_type != "application/octet-stream"
        ):
            if file.original_mime_type != file.mime_type:
                issues.append(
                    f"client declared mime type '{file.original_mime_type}' "
                    f"but actual mime type is '{file.mime_type}'"
                )

        if not issues:
            return None

        return ScanResult(
            file_id=file.id,
            check_name="mime_mismatch",
            status="suspicious",
            message="; ".join(issues),
        )
