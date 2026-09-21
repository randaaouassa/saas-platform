import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.events.publisher import emit
from app.core.uow import UnitOfWork
from app.modules.drivers.models import (
    Driver,
    DriverPosition,
    DriverShift,
    Vehicle,
)
from app.modules.drivers.schemas import (
    DriverCreate,
    DriverUpdate,
    PositionCreate,
    ShiftStart,
    VehicleCreate,
)

DRIVER_STATUSES = {"offline", "available", "assigned", "on_delivery", "on_break"}
VEHICLE_TYPES = {"bike", "van", "truck_small", "truck_large"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_driver(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: DriverCreate
) -> Driver:
    db = uow.session
    d = Driver(
        organization_id=org_id,
        user_id=payload.user_id,
        full_name=payload.full_name,
        phone=payload.phone,
        license_no=payload.license_no,
        status="offline",
    )
    db.add(d)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="driver.created", resource="driver", resource_id=str(d.id))
    uow.commit()
    db.refresh(d)
    return d


def list_drivers(
    uow: UnitOfWork, org_id: uuid.UUID, status: str | None = None
) -> list[Driver]:
    q = select(Driver).where(Driver.organization_id == org_id)
    if status:
        q = q.where(Driver.status == status)
    return list(uow.session.scalars(q.order_by(Driver.created_at)))


def get_driver(uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID) -> Driver:
    d = uow.session.scalar(
        select(Driver).where(Driver.id == driver_id, Driver.organization_id == org_id)
    )
    if not d:
        raise NotFoundError("driver not found")
    return d


def update_driver(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, driver_id: uuid.UUID,
    payload: DriverUpdate,
) -> Driver:
    d = get_driver(uow, org_id, driver_id)
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in DRIVER_STATUSES:
        raise ValidationError_(f"invalid status: {data['status']}")
    for k, v in data.items():
        setattr(d, k, v)
    emit(
        uow.session, type="driver.updated", aggregate_type="driver", aggregate_id=d.id,
        organization_id=org_id, actor_id=actor_id, payload={"status": d.status},
    )
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="driver.updated", resource="driver", resource_id=str(d.id))
    uow.commit()
    uow.session.refresh(d)
    return d


def create_vehicle(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: VehicleCreate
) -> Vehicle:
    db = uow.session
    if payload.type not in VEHICLE_TYPES:
        raise ValidationError_(f"invalid vehicle type: {payload.type}")
    if payload.driver_id:
        get_driver(uow, org_id, payload.driver_id)

    exists = db.scalar(
        select(Vehicle).where(Vehicle.organization_id == org_id, Vehicle.plate == payload.plate)
    )
    if exists:
        raise ConflictError("plate already exists")

    v = Vehicle(
        organization_id=org_id,
        driver_id=payload.driver_id,
        plate=payload.plate,
        type=payload.type,
        capacity_weight=payload.capacity_weight,
        capacity_volume=payload.capacity_volume,
    )
    db.add(v)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="vehicle.created", resource="vehicle", resource_id=str(v.id))
    uow.commit()
    db.refresh(v)
    return v


def list_vehicles(uow: UnitOfWork, org_id: uuid.UUID) -> list[Vehicle]:
    return list(
        uow.session.scalars(
            select(Vehicle).where(Vehicle.organization_id == org_id).order_by(Vehicle.created_at)
        )
    )


def start_shift(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: ShiftStart
) -> DriverShift:
    db = uow.session
    d = get_driver(uow, org_id, payload.driver_id)

    active = db.scalar(
        select(DriverShift).where(
            DriverShift.organization_id == org_id,
            DriverShift.driver_id == d.id,
            DriverShift.status == "active",
        )
    )
    if active:
        raise ConflictError("driver already has an active shift")

    shift = DriverShift(
        organization_id=org_id,
        driver_id=d.id,
        started_at=_now(),
        status="active",
    )
    db.add(shift)
    d.status = "available"
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="shift.started", resource="driver_shift", resource_id=str(shift.id))
    uow.commit()
    db.refresh(shift)
    return shift


def end_shift(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, shift_id: uuid.UUID
) -> DriverShift:
    db = uow.session
    shift = db.scalar(
        select(DriverShift).where(
            DriverShift.id == shift_id, DriverShift.organization_id == org_id
        )
    )
    if not shift:
        raise NotFoundError("shift not found")
    if shift.status != "active":
        raise ConflictError("shift is not active")

    shift.status = "ended"
    shift.ended_at = _now()
    d = get_driver(uow, org_id, shift.driver_id)
    if d.status in {"available", "assigned", "on_delivery", "on_break"}:
        d.status = "offline"

    record(db, organization_id=org_id, actor_id=actor_id,
           action="shift.ended", resource="driver_shift", resource_id=str(shift.id))
    uow.commit()
    db.refresh(shift)
    return shift


def list_shifts(
    uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID | None = None
) -> list[DriverShift]:
    q = select(DriverShift).where(DriverShift.organization_id == org_id)
    if driver_id:
        q = q.where(DriverShift.driver_id == driver_id)
    return list(uow.session.scalars(q.order_by(DriverShift.started_at.desc())))


def record_position(
    uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID, payload: PositionCreate
) -> DriverPosition:
    db = uow.session
    get_driver(uow, org_id, driver_id)
    pos = DriverPosition(
        organization_id=org_id,
        driver_id=driver_id,
        lat=payload.lat,
        lng=payload.lng,
        heading=payload.heading,
        speed=payload.speed,
    )
    db.add(pos)
    emit(
        db, type="driver.location_updated", aggregate_type="driver", aggregate_id=driver_id,
        organization_id=org_id, actor_id=driver_id,
        payload={"lat": payload.lat, "lng": payload.lng},
    )
    uow.commit()
    db.refresh(pos)
    return pos


def latest_position(
    uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID
) -> DriverPosition | None:
    return uow.session.scalar(
        select(DriverPosition)
        .where(
            DriverPosition.organization_id == org_id,
            DriverPosition.driver_id == driver_id,
        )
        .order_by(DriverPosition.recorded_at.desc())
        .limit(1)
    )


def list_positions(
    uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID, limit: int = 100
) -> list[DriverPosition]:
    get_driver(uow, org_id, driver_id)
    return list(
        uow.session.scalars(
            select(DriverPosition)
            .where(
                DriverPosition.organization_id == org_id,
                DriverPosition.driver_id == driver_id,
            )
            .order_by(DriverPosition.recorded_at.desc())
            .limit(limit)
        )
    )