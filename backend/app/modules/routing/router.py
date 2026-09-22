import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.routing import service
from app.modules.routing.schemas import (
    RouteCreate,
    RouteOut,
    RouteRecalcRequest,
    RouteRecalculationOut,
    StopAdd,
    StopOut,
    StopStatusUpdate,
)

router = APIRouter(prefix="/routes", tags=["routing"])

DISPATCHER = require_roles("org_admin", "dispatcher")


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    payload: RouteCreate,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    r = service.create_route(
        uow, user.organization_id, user.id,
        payload.driver_id, payload.date, payload.delivery_ids,
    )
    return RouteOut.model_validate(r)


@router.get("", response_model=list[RouteOut])
def list_routes(
    driver_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[RouteOut]:
    return [
        RouteOut.model_validate(r)
        for r in service.list_routes(uow, user.organization_id, driver_id)
    ]


@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.get_route(uow, user.organization_id, route_id)
    )


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    route_id: uuid.UUID,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    service.delete_route(uow, user.organization_id, user.id, route_id)


@router.post("/{route_id}/start", response_model=RouteOut)
def start_route(
    route_id: uuid.UUID,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.start_route(uow, user.organization_id, user.id, route_id)
    )


@router.post("/{route_id}/complete", response_model=RouteOut)
def complete_route(
    route_id: uuid.UUID,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.complete_route(uow, user.organization_id, user.id, route_id)
    )


@router.post("/{route_id}/stops", response_model=RouteOut)
def add_stop(
    route_id: uuid.UUID,
    payload: StopAdd,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.add_stop(
            uow, user.organization_id, user.id,
            route_id, payload.delivery_id, payload.position,
        )
    )


@router.delete("/{route_id}/stops/{stop_id}", response_model=RouteOut)
def remove_stop(
    route_id: uuid.UUID,
    stop_id: uuid.UUID,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.remove_stop(uow, user.organization_id, user.id, route_id, stop_id)
    )


@router.patch("/stops/{stop_id}/status", response_model=StopOut)
def update_stop_status(
    stop_id: uuid.UUID,
    payload: StopStatusUpdate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> StopOut:
    return StopOut.model_validate(
        service.update_stop_status(uow, user.organization_id, user.id, stop_id, payload.status)
    )


@router.post("/{route_id}/recalculate", response_model=RouteOut)
def recalculate(
    route_id: uuid.UUID,
    payload: RouteRecalcRequest,
    user: User = Depends(DISPATCHER),
    uow: UnitOfWork = Depends(get_uow),
) -> RouteOut:
    return RouteOut.model_validate(
        service.recalculate(uow, user.organization_id, user.id, route_id, payload.reason)
    )


@router.get("/{route_id}/recalculations", response_model=list[RouteRecalculationOut])
def list_recalculations(
    route_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[RouteRecalculationOut]:
    return [
        RouteRecalculationOut.model_validate(r)
        for r in service.list_recalculations(uow, user.organization_id, route_id)
    ]