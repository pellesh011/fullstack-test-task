from enum import StrEnum


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FileStatus(StrEnum):
    NEW = "new"
    PROCESSING = "processing"
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"


class ProcessingTaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineType(StrEnum):
    DEFAULT_FILE_PROCESSING = "default_file_processing"
    EXTENDED_FILE_PROCESSING = "extended_file_processing"


class ProcessorType(StrEnum):
    METADATA_EXTRACTOR = "metadata_extractor"
    SIZE_CHECKER = "size_checker"
    EXTENSION_VALIDATOR = "extension_validator"
    MIME_VALIDATOR = "mime_validator"
    ANTIVIRUS_SCANNER = "antivirus_scanner"
    YARA_SCANNER = "yara_scanner"


class TaskExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"
