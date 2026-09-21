import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.drivers import service
from app.modules.drivers.schemas import (
    DriverCreate,
    DriverOut,
    DriverUpdate,
    PositionCreate,
    PositionOut,
    ShiftOut,
    ShiftStart,
    VehicleCreate,
    VehicleOut,
)
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User

router = APIRouter(prefix="/drivers", tags=["drivers"])

MANAGER = require_roles("org_admin", "dispatcher")


# ---------- Driver ----------
@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> DriverOut:
    return DriverOut.model_validate(
        service.create_driver(uow, user.organization_id, user.id, payload)
    )


@router.get("", response_model=list[DriverOut])
def list_drivers(
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DriverOut]:
    return [
        DriverOut.model_validate(d)
        for d in service.list_drivers(uow, user.organization_id, status_filter)
    ]


@router.get("/me", response_model=DriverOut)
def my_driver(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DriverOut:
    return DriverOut.model_validate(
        service.get_my_driver(uow, user.organization_id, user.id)
    )


@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(
    driver_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DriverOut:
    return DriverOut.model_validate(
        service.get_driver(uow, user.organization_id, driver_id)
    )


@router.patch("/{driver_id}", response_model=DriverOut)
def update_driver(
    driver_id: uuid.UUID,
    payload: DriverUpdate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> DriverOut:
    return DriverOut.model_validate(
        service.update_driver(uow, user.organization_id, user.id, driver_id, payload)
    )


# ---------- Vehicle ----------
@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> VehicleOut:
    return VehicleOut.model_validate(
        service.create_vehicle(uow, user.organization_id, user.id, payload)
    )


@router.get("/vehicles/list", response_model=list[VehicleOut])
def list_vehicles(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[VehicleOut]:
    return [
        VehicleOut.model_validate(v)
        for v in service.list_vehicles(uow, user.organization_id)
    ]


# ---------- Shift ----------
@router.post("/shifts/start", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
def start_shift(
    payload: ShiftStart,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> ShiftOut:
    return ShiftOut.model_validate(
        service.start_shift(uow, user.organization_id, user.id, payload)
    )


@router.post("/shifts/{shift_id}/end", response_model=ShiftOut)
def end_shift(
    shift_id: uuid.UUID,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> ShiftOut:
    return ShiftOut.model_validate(
        service.end_shift(uow, user.organization_id, user.id, shift_id)
    )


@router.get("/shifts/list", response_model=list[ShiftOut])
def list_shifts(
    driver_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[ShiftOut]:
    return [
        ShiftOut.model_validate(s)
        for s in service.list_shifts(uow, user.organization_id, driver_id)
    ]


# ---------- Position ----------
@router.post(
    "/{driver_id}/positions", response_model=PositionOut, status_code=status.HTTP_201_CREATED
)
def record_position(
    driver_id: uuid.UUID,
    payload: PositionCreate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PositionOut:
    return PositionOut.model_validate(
        service.record_position(uow, user.organization_id, driver_id, payload)
    )


@router.get("/{driver_id}/positions/latest", response_model=PositionOut | None)
def latest_position(
    driver_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PositionOut | None:
    pos = service.latest_position(uow, user.organization_id, driver_id)
    return PositionOut.model_validate(pos) if pos else None


@router.get("/{driver_id}/positions", response_model=list[PositionOut])
def list_positions(
    driver_id: uuid.UUID,
    limit: int = 100,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[PositionOut]:
    return [
        PositionOut.model_validate(p)
        for p in service.list_positions(uow, user.organization_id, driver_id, limit)
    ]