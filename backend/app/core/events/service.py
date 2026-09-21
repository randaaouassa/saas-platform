from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events.models import DomainEvent


def fetch_unpublished(db: Session, limit: int = 100) -> list[DomainEvent]:
    return list(
        db.scalars(
            select(DomainEvent)
            .where(DomainEvent.published_at.is_(None))
            .order_by(DomainEvent.created_at)
            .limit(limit)
        )
    )


def mark_published(db: Session, event_ids: list) -> None:
    if not event_ids:
        return
    now = datetime.now(timezone.utc)
    for e in db.scalars(select(DomainEvent).where(DomainEvent.id.in_(event_ids))):
        e.published_at = now
    db.commit()