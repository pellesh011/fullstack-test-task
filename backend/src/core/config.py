import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_db: str = "filehost"
    pgport: str = "5432"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    storage_dir: str = str(
        Path(__file__).resolve().parent.parent.parent / "storage" / "files"
    )

    max_file_size_mb: int = 10
    suspicious_extensions: list[str] = [".exe", ".bat", ".cmd", ".sh", ".js"]
    redis_reconnect_delay: float = 3.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def resolved_redis_url(self) -> str:
        return os.environ.get("CELERY_BROKER_URL", self.celery_broker_url or self.redis_url)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.pgport}/{self.postgres_db}"
        )

    @property
    def resolved_storage_dir(self) -> Path:
        return Path(self.storage_dir)


settings = Settings()
