class DomainException(Exception):
    """Base exception for domain layer."""


class FileNotFoundError(DomainException):
    """Raised when a file entity is not found."""


class StoredFileNotFoundError(DomainException):
    """Raised when a stored file is not found in storage."""


class FileEmptyError(DomainException):
    """Raised when an uploaded file is empty."""


class FileSizeWarningError(DomainException):
    """Raised when file size exceeds warning threshold."""
