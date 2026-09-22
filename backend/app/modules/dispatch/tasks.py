import structlog

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.uow import UnitOfWork
from app.modules.dispatch.service import auto_dispatch_pending
from app.modules.identity.models import Organization

log = structlog.get_logger("dispatch.tasks")


@celery_app.task(name="dispatch.auto_pending", queue="routing")
def auto_dispatch_task(org_id: str) -> int:
    import uuid

    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        n = auto_dispatch_pending(uow, uuid.UUID(org_id))
        log.info("auto_dispatch_done", org=org_id, assigned=n)
        return n
    finally:
        session.close()


@celery_app.task(name="dispatch.auto_all", queue="routing")
def auto_dispatch_all() -> dict:
    from sqlalchemy import select

    session = SessionLocal()
    try:
        org_ids = [str(r) for r in session.scalars(select(Organization.id))]
    finally:
        session.close()

    for oid in org_ids:
        auto_dispatch_task.delay(oid)
    return {"orgs": len(org_ids)}