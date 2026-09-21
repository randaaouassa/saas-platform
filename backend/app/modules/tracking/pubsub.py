import json
import uuid

import structlog
from redis import Redis
from redis.client import PubSub

from app.core.config import settings

log = structlog.get_logger("pubsub")


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def org_channel(org_id: uuid.UUID, topic: str) -> str:
    return f"ws:org:{org_id}:{topic}"


def publish(org_id: uuid.UUID, topic: str, payload: dict) -> None:
    client = _redis()
    try:
        client.publish(org_channel(org_id, topic), json.dumps(payload, default=str))
    except Exception as e:
        log.warning("publish_failed", error=str(e), topic=topic)


def subscribe(org_id: uuid.UUID, topics: list[str]) -> PubSub:
    client = _redis()
    pubsub = client.pubsub()
    channels = [org_channel(org_id, t) for t in topics]
    pubsub.subscribe(*channels)
    return pubsub