import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.uow import UnitOfWork
from app.modules.warehouse.models import Location, Warehouse, WarehouseTask, Zone
from app.modules.warehouse.schemas import (
    LocationCreate,
    TaskCreate,
    WarehouseCreate,
    WarehouseUpdate,
    ZoneCreate,
)

TASK_TYPES = {"receiving", "pick", "pack", "transfer", "adjust"}
TASK_STATUSES = {"pending", "in_progress", "completed", "cancelled"}


def _now() -> datetime:
    return datetime.now(UTC)


# ---------- Warehouse ----------
def create_warehouse(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: WarehouseCreate) -> Warehouse:
    db = uow.session
    exists = db.scalar(
        select(Warehouse).where(Warehouse.organization_id == org_id, Warehouse.code == payload.code)
    )
    if exists:
        raise ConflictError("warehouse code already exists")

    wh = Warehouse(
        organization_id=org_id,
        name=payload.name,
        code=payload.code,
        address=payload.address,
        lat=payload.lat,
        lng=payload.lng,
        timezone=payload.timezone,
    )
    db.add(wh)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="warehouse.created", resource="warehouse", resource_id=str(wh.id))
    uow.commit()
    db.refresh(wh)
    return wh


def list_warehouses(uow: UnitOfWork, org_id: uuid.UUID) -> list[Warehouse]:
    return list(
        uow.session.scalars(
            select(Warehouse).where(Warehouse.organization_id == org_id).order_by(Warehouse.created_at)
        )
    )


def get_warehouse(uow: UnitOfWork, org_id: uuid.UUID, warehouse_id: uuid.UUID) -> Warehouse:
    wh = uow.session.scalar(
        select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.organization_id == org_id)
    )
    if not wh:
        raise NotFoundError("warehouse not found")
    return wh


def update_warehouse(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, warehouse_id: uuid.UUID, payload: WarehouseUpdate
) -> Warehouse:
    wh = get_warehouse(uow, org_id, warehouse_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wh, field, value)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="warehouse.updated", resource="warehouse", resource_id=str(wh.id))
    uow.commit()
    uow.session.refresh(wh)
    return wh


# ---------- Zone ----------
def create_zone(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, warehouse_id: uuid.UUID, payload: ZoneCreate
) -> Zone:
    get_warehouse(uow, org_id, warehouse_id)
    exists = uow.session.scalar(
        select(Zone).where(Zone.warehouse_id == warehouse_id, Zone.code == payload.code)
    )
    if exists:
        raise ConflictError("zone code already exists in this warehouse")

    zone = Zone(
        organization_id=org_id,
        warehouse_id=warehouse_id,
        name=payload.name,
        code=payload.code,
        type=payload.type,
    )
    uow.session.add(zone)
    uow.flush()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="zone.created", resource="zone", resource_id=str(zone.id))
    uow.commit()
    uow.session.refresh(zone)
    return zone


def list_zones(uow: UnitOfWork, org_id: uuid.UUID, warehouse_id: uuid.UUID) -> list[Zone]:
    get_warehouse(uow, org_id, warehouse_id)
    return list(
        uow.session.scalars(
            select(Zone).where(Zone.organization_id == org_id, Zone.warehouse_id == warehouse_id)
        )
    )


# ---------- Location ----------
def create_location(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, zone_id: uuid.UUID, payload: LocationCreate
) -> Location:
    zone = uow.session.scalar(
        select(Zone).where(Zone.id == zone_id, Zone.organization_id == org_id)
    )
    if not zone:
        raise NotFoundError("zone not found")

    exists = uow.session.scalar(
        select(Location).where(Location.zone_id == zone_id, Location.code == payload.code)
    )
    if exists:
        raise ConflictError("location code already exists in this zone")

    loc = Location(
        organization_id=org_id,
        zone_id=zone_id,
        code=payload.code,
        kind=payload.kind,
        capacity=payload.capacity,
    )
    uow.session.add(loc)
    uow.flush()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="location.created", resource="location", resource_id=str(loc.id))
    uow.commit()
    uow.session.refresh(loc)
    return loc


def list_locations(uow: UnitOfWork, org_id: uuid.UUID, zone_id: uuid.UUID) -> list[Location]:
    return list(
        uow.session.scalars(
            select(Location).where(Location.organization_id == org_id, Location.zone_id == zone_id)
        )
    )


# ---------- Task ----------
def create_task(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: TaskCreate) -> WarehouseTask:
    get_warehouse(uow, org_id, payload.warehouse_id)
    if payload.type not in TASK_TYPES:
        raise ValidationError_(f"invalid task type: {payload.type}")

    task = WarehouseTask(
        organization_id=org_id,
        warehouse_id=payload.warehouse_id,
        type=payload.type,
        ref_type=payload.ref_type,
        ref_id=payload.ref_id,
        assigned_to=payload.assigned_to,
        status="pending",
    )
    uow.session.add(task)
    uow.flush()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="warehouse_task.created", resource="warehouse_task", resource_id=str(task.id))
    uow.commit()
    uow.session.refresh(task)
    return task


def set_task_status(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, task_id: uuid.UUID, status: str
) -> WarehouseTask:
    if status not in TASK_STATUSES:
        raise ValidationError_(f"invalid task status: {status}")
    task = uow.session.scalar(
        select(WarehouseTask).where(WarehouseTask.id == task_id, WarehouseTask.organization_id == org_id)
    )
    if not task:
        raise NotFoundError("task not found")

    task.status = status
    if status == "in_progress" and task.started_at is None:
        task.started_at = _now()
    if status in {"completed", "cancelled"}:
        task.completed_at = _now()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action=f"warehouse_task.{status}", resource="warehouse_task", resource_id=str(task.id))
    uow.commit()
    uow.session.refresh(task)
    return task


def list_tasks(
    uow: UnitOfWork,
    org_id: uuid.UUID,
    warehouse_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[WarehouseTask]:
    q = select(WarehouseTask).where(WarehouseTask.organization_id == org_id)
    if warehouse_id:
        q = q.where(WarehouseTask.warehouse_id == warehouse_id)
    if status:
        q = q.where(WarehouseTask.status == status)
    return list(uow.session.scalars(q.order_by(WarehouseTask.created_at)))