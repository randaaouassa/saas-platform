from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import delete

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.events.models import DomainEvent
from app.modules.drivers.models import DriverPosition

log = structlog.get_logger("cleanup.tasks")


@celery_app.task(name="default.cleanup_old_driver_positions", queue="default")
def cleanup_old_driver_positions(days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    session = SessionLocal()
    try:
        result = session.execute(
            delete(DriverPosition).where(DriverPosition.recorded_at < cutoff)
        )
        session.commit()
        log.info("cleanup_positions", deleted=result.rowcount, days=days)
        return result.rowcount or 0
    finally:
        session.close()


@celery_app.task(name="default.cleanup_old_domain_events", queue="default")
def cleanup_old_domain_events(days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    session = SessionLocal()
    try:
        result = session.execute(
            delete(DomainEvent).where(
                DomainEvent.published_at.is_not(None),
                DomainEvent.created_at < cutoff,
            )
        )
        session.commit()
        log.info("cleanup_events", deleted=result.rowcount, days=days)
        return result.rowcount or 0
    finally:
        session.close()