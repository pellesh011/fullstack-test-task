import json
import logging
import threading
import time

from redis import from_url
from redis.exceptions import ConnectionError

from src.core.config import settings

logger = logging.getLogger(__name__)


class TaskRegistry:
    _tasks = {}

    @classmethod
    def register(cls, name: str, task):
        cls._tasks[name] = task

    @classmethod
    def get(cls, name: str):
        return cls._tasks.get(name)


def _listen():
    retry_delay = settings.redis_reconnect_delay
    while True:
        try:
            r = from_url(settings.resolved_redis_url)
            r.ping()
        except ConnectionError:
            logger.warning(
                "event subscriber: redis unavailable, retrying in %s s",
                retry_delay,
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30.0)
            continue

        retry_delay = settings.redis_reconnect_delay
        logger.info("event subscriber: listening for file_events")
        try:
            while True:
                _, data = r.blpop("file_events", timeout=0)
                try:
                    payload = json.loads(data)
                    if payload.get("event") == "FileCreated":
                        file_id = payload.get("file_id")
                        if file_id:
                            scan_task = TaskRegistry.get("scan_file_for_threats")
                            if scan_task:
                                scan_task.delay(file_id)
                            else:
                                logger.warning(
                                    "scan_file_for_threats task not registered"
                                )
                except Exception:
                    logger.exception("event subscriber: failed to process event")
        except ConnectionError:
            logger.warning("event subscriber: redis connection lost, reconnecting...")


def start_event_subscriber() -> None:
    thread = threading.Thread(target=_listen, daemon=True)
    thread.start()
    logger.info("event subscriber thread started")
