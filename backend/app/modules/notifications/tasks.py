import structlog

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.uow import UnitOfWork
from app.modules.notifications import service
from app.modules.notifications.providers import dispatch
from app.modules.notifications.schemas import NotificationCreate

log = structlog.get_logger("notifications.tasks")


@celery_app.task(
    name="notifications.dispatch",
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    queue="notifications",
)
def dispatch_notification(self, org_id: str, actor_id: str | None, payload: dict) -> str:
    import uuid

    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        n = service.create_notification(
            uow,
            uuid.UUID(org_id),
            uuid.UUID(actor_id) if actor_id else None,
            NotificationCreate(**payload),
        )
        log.info("notification_dispatched", id=str(n.id), channel=n.channel)
        return str(n.id)
    except Exception as e:
        log.warning("notification_dispatch_failed", error=str(e))
        raise self.retry(exc=e)
    finally:
        session.close()


@celery_app.task(name="notifications.process_deliveries", queue="notifications")
def process_deliveries(limit: int = 50) -> int:
    """Send queued notification_deliveries via providers, update status."""
    from sqlalchemy import select

    from app.modules.notifications.models import Notification, NotificationDelivery

    session = SessionLocal()
    processed = 0
    try:
        uow = UnitOfWork(session)
        db = session
        rows = list(
            db.scalars(
                select(NotificationDelivery)
                .where(NotificationDelivery.status == "pending")
                .order_by(NotificationDelivery.created_at)
                .limit(limit)
            )
        )
        for d in rows:
            n = db.get(Notification, d.notification_id)
            if not n:
                continue
            subject = n.template
            body = str(n.payload_json)
            target = None
            try:
                result = dispatch(d.provider, target, subject, body)
                service.mark_delivery_sent(
                    uow, n.organization_id, d.id,
                    provider_msg_id=result.get("msg_id"),
                )
                processed += 1
            except Exception as e:
                service.mark_delivery_sent(
                    uow, n.organization_id, d.id, error=str(e)
                )
        return processed
    finally:
        session.close()