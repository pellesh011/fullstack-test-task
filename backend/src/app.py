from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, DBAPIError
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from src.core.config import settings
from src.presentation.routes import router
from src.infrastructure.database import DatabaseSessionManager

app = FastAPI(
    title="File Share API",
    version="1.0.0",
    description="MVP file sharing service with threat scanning and alerts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_parsed,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

_db_manager: DatabaseSessionManager | None = None


def get_db_manager() -> DatabaseSessionManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseSessionManager()
    return _db_manager


@app.exception_handler(OperationalError)
@app.exception_handler(DBAPIError)
async def db_connection_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database unavailable, please try again later"},
    )


@app.exception_handler(RedisConnectionError)
@app.exception_handler(RedisError)
async def redis_connection_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Event service unavailable, please try again later"},
    )


@app.get("/health")
async def health_check() -> JSONResponse:
    db_ok = False
    redis_ok = False

    try:
        manager = get_db_manager()
        async with manager.session() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        import redis.asyncio as redis

        r = redis.from_url(settings.resolved_redis_url)
        await r.ping()
        await r.close()
        redis_ok = True
    except Exception:
        pass

    status_code = (
        status.HTTP_200_OK
        if (db_ok and redis_ok)
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if (db_ok and redis_ok) else "degraded",
            "database": "ok" if db_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
        },
    )


app.include_router(router)
