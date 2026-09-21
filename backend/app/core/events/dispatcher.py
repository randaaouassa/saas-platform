import structlog
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.events import service
from app.core.events.models import DomainEvent
from app.modules.tracking.pubsub import publish

log = structlog.get_logger("events.dispatcher")

TOPIC_MAP = {
    "order.": "dispatcher",
    "delivery.": "delivery",
    "driver.": "driver",
    "route.": "dispatcher",
    "notification.": "notification",
    "stock.": "dispatcher",
    "product.": "dispatcher",
    "warehouse.": "dispatcher",
}


def _topic_for(event_type: str) -> str | None:
    for prefix, topic in TOPIC_MAP.items():
        if event_type.startswith(prefix):
            return topic
    return None


def _envelope(e: DomainEvent) -> dict:
    return {
        "event_id": str(e.id),
        "type": e.type,
        "occurred_at": e.created_at.isoformat() if e.created_at else None,
        "org_id": str(e.organization_id) if e.organization_id else None,
        "actor_id": str(e.actor_id) if e.actor_id else None,
        "aggregate_type": e.aggregate_type,
        "aggregate_id": str(e.aggregate_id),
        "version": e.version,
        "payload": e.payload,
    }


def dispatch_once(batch_size: int = 100, session: Session | None = None) -> int:
    own = session is None
    db = session or SessionLocal()
    try:
        events = service.fetch_unpublished(db, batch_size)
        if not events:
            return 0

        published_ids = []
        for e in events:
            topic = _topic_for(e.type)
            if topic and e.organization_id:
                try:
                    publish(e.organization_id, topic, _envelope(e))
                except Exception as ex:
                    log.warning("publish_failed", error=str(ex), event_id=str(e.id))
                    continue
            published_ids.append(e.id)

        service.mark_published(db, published_ids)
        log.info("events_dispatched", count=len(published_ids))
        return len(published_ids)
    finally:
        if own:
            db.close()