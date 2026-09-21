import structlog

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.uow import UnitOfWork
from app.modules.analytics.service import rebuild_day

log = structlog.get_logger("analytics.tasks")


@celery_app.task(name="analytics.rebuild_day", queue="analytics")
def rebuild_day_task(org_id: str, day_iso: str) -> dict:
    import uuid
    from datetime import date

    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        result = rebuild_day(uow, uuid.UUID(org_id), date.fromisoformat(day_iso))
        log.info("analytics_rebuilt", org=org_id, date=day_iso)
        return {**result, "date": result["date"].isoformat()}
    finally:
        session.close()