import structlog

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.uow import UnitOfWork
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationCreate

log = structlog.get_logger("notifications.tasks")


@celery_app.task(
    name="notifications.dispatch",
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    queue="notifications",
)
def dispatch_notification(
    self, org_id: str, actor_id: str | None, payload: dict
) -> str:
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