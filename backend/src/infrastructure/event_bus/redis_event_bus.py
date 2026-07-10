import json

from redis.asyncio import from_url

from src.domain.events import FileCreated
from src.domain.interfaces.event_bus import EventBus


class RedisEventBus(EventBus):
    def __init__(self, redis_url: str):
        self._redis = from_url(redis_url)

    async def publish(self, event) -> None:
        if isinstance(event, FileCreated):
            payload = json.dumps({"event": "FileCreated", "file_id": event.file_id})
        else:
            raise ValueError(f"Unknown event type: {type(event)}")

        await self._redis.rpush("file_events", payload)
