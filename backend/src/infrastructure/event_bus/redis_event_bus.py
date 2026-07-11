import asyncio
import json
import logging
from typing import Any, Optional

from redis.asyncio import from_url
from redis.exceptions import ConnectionError as RedisConnectionError

from src.domain.events import FileCreated
from src.domain.interfaces.event_bus import EventBus

logger = logging.getLogger(__name__)


class RedisEventBus(EventBus):
    def __init__(self, redis_url: str, max_retries: int = 3, base_delay: float = 0.1):
        self._redis = from_url(redis_url)
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def publish(self, event: Any) -> None:
        if isinstance(event, FileCreated):
            payload = json.dumps({"event": "FileCreated", "file_id": event.file_id})
        else:
            raise ValueError(f"Unknown event type: {type(event)}")

        last_exception: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                await self._redis.rpush("file_events", payload)
                return
            except RedisConnectionError as e:
                last_exception = e
                delay = self._base_delay * (2**attempt)
                logger.warning(
                    "RedisEventBus: publish failed (attempt %d/%d), retrying in %.2fs: %s",
                    attempt + 1,
                    self._max_retries,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)

        logger.error(
            "RedisEventBus: publish failed after %d retries", self._max_retries
        )
        if last_exception:
            raise last_exception
        raise RuntimeError("RedisEventBus: publish failed")
