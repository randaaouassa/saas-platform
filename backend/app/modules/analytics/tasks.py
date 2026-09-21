import structlog
from datetime import date, timedelta

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.uow import UnitOfWork
from app.modules.analytics.service import rebuild_day
from app.modules.identity.models import Organization

log = structlog.get_logger("analytics.tasks")


@celery_app.task(name="analytics.rebuild_day", queue="analytics")
def rebuild_day_task(org_id: str, day_iso: str) -> dict:
    import uuid

    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        result = rebuild_day(uow, uuid.UUID(org_id), date.fromisoformat(day_iso))
        log.info("analytics_rebuilt", org=org_id, date=day_iso)
        return {**result, "date": result["date"].isoformat()}
    finally:
        session.close()


@celery_app.task(name="analytics.rebuild_all_yesterday", queue="analytics")
def rebuild_all_yesterday() -> dict:
    from sqlalchemy import select

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    session = SessionLocal()
    try:
        org_ids = [str(r) for r in session.scalars(select(Organization.id))]
    finally:
        session.close()

    for oid in org_ids:
        rebuild_day_task.delay(oid, yesterday)

    log.info("analytics_fanout", count=len(org_ids), date=yesterday)
    return {"orgs": len(org_ids), "date": yesterday}