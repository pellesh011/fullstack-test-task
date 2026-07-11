import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_comma_separated(v: str | list[str]) -> list[str]:
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_db: str = "filehost"
    pgport: str = "5432"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    storage_dir: str = str(
        Path(__file__).resolve().parent.parent.parent / "storage" / "files"
    )

    max_file_size_mb: int = 10
    max_file_size_warning_mb: int = 8192
    suspicious_extensions: str = ".exe,.bat,.cmd,.sh,.js"
    redis_reconnect_delay: float = 3.0

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True

    @property
    def cors_origins_parsed(self) -> list[str]:
        return parse_comma_separated(self.cors_origins)

    @property
    def suspicious_extensions_parsed(self) -> list[str]:
        return parse_comma_separated(self.suspicious_extensions)

    @property
    def resolved_redis_url(self) -> str:
        return os.environ.get(
            "CELERY_BROKER_URL", self.celery_broker_url or self.redis_url
        )

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
