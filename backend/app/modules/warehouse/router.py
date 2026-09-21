import uuid
from typing import Literal

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.warehouse import service
from app.modules.warehouse.schemas import (
    LocationCreate,
    LocationOut,
    TaskCreate,
    TaskOut,
    TaskStatusUpdate,
    WarehouseCreate,
    WarehouseOut,
    WarehouseUpdate,
    ZoneCreate,
    ZoneOut,
)

router = APIRouter(prefix="/warehouses", tags=["warehouse"])

MANAGER = require_roles("org_admin", "warehouse_manager")


# ---------- Warehouse ----------
@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> WarehouseOut:
    return WarehouseOut.model_validate(
        service.create_warehouse(uow, user.organization_id, user.id, payload)
    )


@router.get("", response_model=list[WarehouseOut])
def list_warehouses(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[WarehouseOut]:
    return [
        WarehouseOut.model_validate(w)
        for w in service.list_warehouses(uow, user.organization_id)
    ]


@router.get("/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(
    warehouse_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> WarehouseOut:
    return WarehouseOut.model_validate(
        service.get_warehouse(uow, user.organization_id, warehouse_id)
    )


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(
    warehouse_id: uuid.UUID,
    payload: WarehouseUpdate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> WarehouseOut:
    return WarehouseOut.model_validate(
        service.update_warehouse(uow, user.organization_id, user.id, warehouse_id, payload)
    )


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: uuid.UUID,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    service.delete_warehouse(uow, user.organization_id, user.id, warehouse_id)


# ---------- Zones ----------
@router.post(
    "/{warehouse_id}/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED
)
def create_zone(
    warehouse_id: uuid.UUID,
    payload: ZoneCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> ZoneOut:
    return ZoneOut.model_validate(
        service.create_zone(uow, user.organization_id, user.id, warehouse_id, payload)
    )


@router.get("/{warehouse_id}/zones", response_model=list[ZoneOut])
def list_zones(
    warehouse_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[ZoneOut]:
    return [
        ZoneOut.model_validate(z)
        for z in service.list_zones(uow, user.organization_id, warehouse_id)
    ]


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: uuid.UUID,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    service.delete_zone(uow, user.organization_id, user.id, zone_id)


# ---------- Locations ----------
@router.post(
    "/zones/{zone_id}/locations",
    response_model=LocationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    zone_id: uuid.UUID,
    payload: LocationCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> LocationOut:
    return LocationOut.model_validate(
        service.create_location(uow, user.organization_id, user.id, zone_id, payload)
    )


@router.get("/zones/{zone_id}/locations", response_model=list[LocationOut])
def list_locations(
    zone_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[LocationOut]:
    return [
        LocationOut.model_validate(loc)
        for loc in service.list_locations(uow, user.organization_id, zone_id)
    ]


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: uuid.UUID,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    service.delete_location(uow, user.organization_id, user.id, location_id)


# ---------- Tasks ----------
@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> TaskOut:
    return TaskOut.model_validate(
        service.create_task(uow, user.organization_id, user.id, payload)
    )


@router.get("/tasks/list", response_model=list[TaskOut])
def list_tasks(
    warehouse_id: uuid.UUID | None = None,
    status_filter: Literal["pending", "in_progress", "completed", "cancelled"] | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[TaskOut]:
    return [
        TaskOut.model_validate(t)
        for t in service.list_tasks(uow, user.organization_id, warehouse_id, status_filter)
    ]


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: uuid.UUID,
    payload: TaskStatusUpdate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> TaskOut:
    return TaskOut.model_validate(
        service.set_task_status(uow, user.organization_id, user.id, task_id, payload.status)
    )