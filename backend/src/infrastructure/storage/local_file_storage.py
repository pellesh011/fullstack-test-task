from pathlib import Path

from src.domain.interfaces.file_storage import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, stored_name: str) -> Path:
        return self._storage_dir / stored_name

    def save(self, stored_name: str, content: bytes) -> Path:
        p = self._path(stored_name)
        p.write_bytes(content)
        return p

    def get_path(self, stored_name: str) -> Path:
        return self._path(stored_name)

    def exists(self, stored_name: str) -> bool:
        return self._path(stored_name).exists()

    def delete(self, stored_name: str) -> bool:
        p = self._path(stored_name)
        if p.exists():
            p.unlink()
            return True
        return False

    def read_bytes(self, stored_name: str) -> bytes:
        return self._path(stored_name).read_bytes()

    def read_text(self, stored_name: str) -> str:
        return self._path(stored_name).read_text(encoding="utf-8", errors="ignore")
