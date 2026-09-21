import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.events.publisher import emit
from app.core.uow import UnitOfWork
from app.modules.deliveries.models import Delivery
from app.modules.dispatch.models import Assignment, DispatchEvent
from app.modules.drivers.models import Driver, DriverPosition, Vehicle

ASSIGNMENT_STATUSES = {"offered", "accepted", "rejected", "expired", "completed"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _get_delivery(uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID) -> Delivery:
    d = uow.session.scalar(
        select(Delivery).where(Delivery.id == delivery_id, Delivery.organization_id == org_id)
    )
    if not d:
        raise NotFoundError("delivery not found")
    return d


def _candidate_score(distance_km: float | None, active_deliveries: int) -> float:
    distance_score = 100.0 if distance_km is None else max(0.0, 100.0 - distance_km * 5.0)
    workload_score = max(0.0, 100.0 - active_deliveries * 20.0)
    return 0.7 * distance_score + 0.3 * workload_score


def rank_candidates(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, delivery_id: uuid.UUID
) -> list[dict]:
    db = uow.session
    delivery = _get_delivery(uow, org_id, delivery_id)

    drivers = list(
        db.scalars(
            select(Driver).where(
                Driver.organization_id == org_id,
                Driver.status.in_(["available", "assigned", "on_delivery"]),
            )
        )
    )

    candidates: list[dict] = []
    for driver in drivers:
        pos = db.scalar(
            select(DriverPosition)
            .where(
                DriverPosition.organization_id == org_id,
                DriverPosition.driver_id == driver.id,
            )
            .order_by(DriverPosition.recorded_at.desc())
            .limit(1)
        )
        distance_km: float | None = None
        if pos and delivery.pickup_lat is not None and delivery.pickup_lng is not None:
            distance_km = _haversine_km(pos.lat, pos.lng, delivery.pickup_lat, delivery.pickup_lng)

        active_count = 0
        for _ in db.scalars(
            select(Assignment).where(
                Assignment.organization_id == org_id,
                Assignment.driver_id == driver.id,
                Assignment.status.in_(["offered", "accepted"]),
            )
        ):
            active_count += 1

        vehicle = db.scalar(
            select(Vehicle).where(Vehicle.organization_id == org_id, Vehicle.driver_id == driver.id)
        )

        score = _candidate_score(distance_km, active_count)

        candidates.append(
            {
                "driver_id": driver.id,
                "full_name": driver.full_name,
                "status": driver.status,
                "vehicle_id": vehicle.id if vehicle else None,
                "distance_km": round(distance_km, 3) if distance_km is not None else None,
                "active_deliveries": active_count,
                "score": round(score, 3),
                "factors": {
                    "distance_km": distance_km,
                    "active_deliveries": active_count,
                },
            }
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)

    for c in candidates:
        db.add(
            DispatchEvent(
                organization_id=org_id,
                delivery_id=delivery_id,
                candidate_driver_id=c["driver_id"],
                score=Decimal(str(c["score"])),
                factors_json={
                    "distance_km": c["factors"]["distance_km"],
                    "active_deliveries": c["factors"]["active_deliveries"],
                },
            )
        )
    record(db, organization_id=org_id, actor_id=actor_id,
           action="dispatch.ranked", resource="delivery", resource_id=str(delivery_id))
    uow.commit()
    return candidates


def assign(
    uow: UnitOfWork,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    delivery_id: uuid.UUID,
    driver_id: uuid.UUID | None,
    vehicle_id: uuid.UUID | None,
    mode: str,
) -> Assignment:
    db = uow.session
    delivery = _get_delivery(uow, org_id, delivery_id)
    if delivery.status not in {"pending", "rescheduled"}:
        raise ConflictError(f"cannot assign delivery in status {delivery.status}")

    if driver_id is None:
        candidates = rank_candidates(uow, org_id, actor_id, delivery_id)
        if not candidates:
            raise NotFoundError("no available drivers")
        driver_id = candidates[0]["driver_id"]
        vehicle_id = vehicle_id or candidates[0]["vehicle_id"]
        mode = "auto"

    driver = db.scalar(
        select(Driver).where(Driver.id == driver_id, Driver.organization_id == org_id)
    )
    if not driver:
        raise NotFoundError("driver not found")
    if driver.status == "offline":
        raise ConflictError("driver is offline")

    assignment = Assignment(
        organization_id=org_id,
        delivery_id=delivery_id,
        driver_id=driver.id,
        vehicle_id=vehicle_id,
        score=Decimal("0"),
        mode=mode,
        status="offered",
        assigned_by=actor_id,
        assigned_at=_now(),
    )
    db.add(assignment)

    emit(
        db, type="delivery.assigned", aggregate_type="delivery", aggregate_id=delivery_id,
        organization_id=org_id, actor_id=actor_id,
        payload={"driver_id": str(driver.id), "mode": mode},
    )
    record(db, organization_id=org_id, actor_id=actor_id,
           action="dispatch.assigned", resource="delivery", resource_id=str(delivery_id))
    uow.commit()
    db.refresh(assignment)
    return assignment


def update_assignment_status(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    assignment_id: uuid.UUID, status: str,
) -> Assignment:
    if status not in ASSIGNMENT_STATUSES:
        raise ValidationError_(f"invalid status: {status}")
    db = uow.session
    a = db.scalar(
        select(Assignment).where(
            Assignment.id == assignment_id, Assignment.organization_id == org_id
        )
    )
    if not a:
        raise NotFoundError("assignment not found")

    a.status = status
    if status == "completed":
        a.completed_at = _now()

    record(db, organization_id=org_id, actor_id=actor_id,
           action=f"assignment.{status}", resource="assignment", resource_id=str(a.id))
    uow.commit()
    db.refresh(a)
    return a


def list_assignments(
    uow: UnitOfWork, org_id: uuid.UUID,
    delivery_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
) -> list[Assignment]:
    q = select(Assignment).where(Assignment.organization_id == org_id)
    if delivery_id:
        q = q.where(Assignment.delivery_id == delivery_id)
    if driver_id:
        q = q.where(Assignment.driver_id == driver_id)
    return list(uow.session.scalars(q.order_by(Assignment.created_at.desc())))