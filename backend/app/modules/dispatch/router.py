import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.dispatch import service
from app.modules.dispatch.schemas import (
    AssignmentOut,
    AssignmentStatusUpdate,
    AssignRequest,
    CandidateOut,
    RankCandidatesRequest,
    RankCandidatesResponse,
)
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

DISPATCHER = require_roles("org_admin", "dispatcher")


@router.post("/candidates", response_model=RankCandidatesResponse)
def rank_candidates(
    payload: RankCandidatesRequest,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RankCandidatesResponse:
    candidates = service.rank_candidates(uow, user.organization_id, user.id, payload.delivery_id)
    return RankCandidatesResponse(
        delivery_id=payload.delivery_id,
        candidates=[CandidateOut(**c) for c in candidates],
    )


@router.post("/assign", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def assign(
    payload: AssignRequest,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> AssignmentOut:
    mode = "manual" if payload.driver_id else "auto"
    a = service.assign(
        uow, user.organization_id, user.id,
        payload.delivery_id, payload.driver_id, payload.vehicle_id, mode,
    )
    return AssignmentOut.model_validate(a)


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(
    delivery_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[AssignmentOut]:
    return [
        AssignmentOut.model_validate(a)
        for a in service.list_assignments(uow, user.organization_id, delivery_id, driver_id)
    ]


@router.patch("/assignments/{assignment_id}/status", response_model=AssignmentOut)
def update_status(
    assignment_id: uuid.UUID,
    payload: AssignmentStatusUpdate,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> AssignmentOut:
    return AssignmentOut.model_validate(
        service.update_assignment_status(uow, user.organization_id, user.id, assignment_id, payload.status)
    )