import uuid

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import require_roles
from app.modules.identity.models import User
from app.modules.system import service
from app.modules.system.schemas import (
    OrgStatusUpdate,
    OrgSummary,
    SystemStats,
    VersionResponse,
)

router = APIRouter(prefix="/system", tags=["system"])

SUPER = require_roles("super_admin")


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(name=settings.APP_NAME, version="0.1.0", env=settings.ENV)


@router.get("/stats", response_model=SystemStats)
def stats(
    user: User = Depends(SUPER),
    uow: UnitOfWork = Depends(get_uow),
) -> SystemStats:
    return SystemStats(**service.system_stats(uow))


@router.get("/orgs", response_model=list[OrgSummary])
def list_orgs(
    user: User = Depends(SUPER),
    uow: UnitOfWork = Depends(get_uow),
) -> list[OrgSummary]:
    return [OrgSummary(**o) for o in service.list_orgs(uow)]


@router.patch("/orgs/{org_id}/status", response_model=OrgSummary)
def update_org_status(
    org_id: uuid.UUID,
    payload: OrgStatusUpdate,
    user: User = Depends(SUPER),
    uow: UnitOfWork = Depends(get_uow),
) -> OrgSummary:
    service.update_org_status(uow, user.id, org_id, payload.status)
    for o in service.list_orgs(uow):
        if o["id"] == org_id:
            return OrgSummary(**o)
    return OrgSummary(
        id=org_id, name="", slug="", plan="", status=payload.status,
        users_count=0, created_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc),
    )