import aiofiles
import aiofiles.os
from pathlib import Path

from src.domain.interfaces.file_storage import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir.resolve()
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, stored_name: str) -> Path:
        safe_name = Path(stored_name).name
        full_path = (self._storage_dir / safe_name).resolve()
        if not full_path.is_relative_to(self._storage_dir):
            raise ValueError(f"Invalid stored_name: path traversal attempt")
        return full_path

    async def save(self, stored_name: str, content: bytes) -> Path:
        p = self._path(stored_name)
        async with aiofiles.open(p, "wb") as f:
            await f.write(content)
        return p

    def get_path(self, stored_name: str) -> Path:
        return self._path(stored_name)

    async def exists(self, stored_name: str) -> bool:
        return await aiofiles.os.path.exists(self._path(stored_name))

    async def delete(self, stored_name: str) -> bool:
        p = self._path(stored_name)
        try:
            await aiofiles.os.unlink(p)
            return True
        except FileNotFoundError:
            return False

    async def read_bytes(self, stored_name: str) -> bytes:
        p = self._path(stored_name)
        async with aiofiles.open(p, "rb") as f:
            return await f.read()

    async def read_text(self, stored_name: str) -> str:
        p = self._path(stored_name)
        async with aiofiles.open(p, "r", encoding="utf-8", errors="ignore") as f:
            return await f.read()