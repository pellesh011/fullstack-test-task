import json
import logging
import threading

from redis import from_url
from redis.exceptions import ConnectionError

from src.core.config import settings

logger = logging.getLogger(__name__)


def _listen():
    while True:
        try:
            r = from_url(settings.resolved_redis_url)
            r.ping()
        except ConnectionError:
            logger.warning(
                "event subscriber: redis unavailable, retrying in %s s",
                settings.redis_reconnect_delay,
            )
            threading.Event().wait(settings.redis_reconnect_delay)
            continue

        logger.info("event subscriber: listening for file_events")
        try:
            while True:
                _, data = r.blpop("file_events", timeout=0)
                try:
                    payload = json.loads(data)
                    if payload.get("event") == "FileCreated":
                        from src.tasks import scan_file_for_threats

                        scan_file_for_threats.delay(payload["file_id"])
                except Exception:
                    logger.exception("event subscriber: failed to process event")
        except ConnectionError:
            logger.warning("event subscriber: redis connection lost, reconnecting...")


def start_event_subscriber() -> None:
    thread = threading.Thread(target=_listen, daemon=True)
    thread.start()
    logger.info("event subscriber thread started")
