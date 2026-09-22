import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.events.publisher import emit
from app.core.uow import UnitOfWork
from app.modules.deliveries.models import (
    Delivery,
    DeliveryStatusHistory,
    Package,
    ProofOfDelivery,
)
from app.modules.deliveries.schemas import (
    DeliveryCancel,
    DeliveryCreate,
    DeliveryReschedule,
    DeliveryStatusUpdate,
    DeliveryUpdate,
    PODCreate,
)
from app.modules.dispatch.models import Assignment

DELIVERY_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"assigned", "cancelled"},
    "assigned": {"picked_up", "cancelled"},
    "picked_up": {"in_transit", "failed"},
    "in_transit": {"delivered", "failed"},
    "delivered": set(),
    "failed": {"rescheduled", "returned"},
    "rescheduled": {"assigned", "cancelled"},
    "returned": set(),
    "cancelled": set(),
}

FINAL_STATES = {"delivered", "returned", "cancelled"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_token() -> str:
    return secrets.token_urlsafe(16)[:22]


def _track(db, org_id: uuid.UUID, delivery_id: uuid.UUID, event_type: str,
           lat: float | None = None, lng: float | None = None, payload: dict | None = None) -> None:
    from app.modules.tracking.models import TrackingEvent

    db.add(
        TrackingEvent(
            organization_id=org_id,
            delivery_id=delivery_id,
            type=event_type,
            lat=lat,
            lng=lng,
            payload_json=payload or {},
        )
    )


def create_delivery(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: DeliveryCreate
) -> Delivery:
    db = uow.session
    d = Delivery(
        organization_id=org_id,
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        pickup_location=payload.pickup_location,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        dropoff_location=payload.dropoff_location,
        dropoff_lat=payload.dropoff_lat,
        dropoff_lng=payload.dropoff_lng,
        scheduled_at=payload.scheduled_at,
        status="pending",
        public_token=_new_token(),
    )
    db.add(d)
    uow.flush()

    for pkg in payload.packages:
        exists = db.scalar(
            select(Package).where(
                Package.organization_id == org_id, Package.code == pkg.code
            )
        )
        if exists:
            raise ConflictError(f"package code already exists: {pkg.code}")
        db.add(
            Package(
                organization_id=org_id,
                delivery_id=d.id,
                code=pkg.code,
                weight=pkg.weight,
                length=pkg.length,
                width=pkg.width,
                height=pkg.height,
                volume=pkg.volume,
            )
        )

    db.add(
        DeliveryStatusHistory(
            organization_id=org_id, delivery_id=d.id,
            from_status=None, to_status="pending", actor_id=actor_id,
        )
    )
    _track(db, org_id, d.id, "pending")
    emit(db, type="delivery.created", aggregate_type="delivery", aggregate_id=d.id,
         organization_id=org_id, actor_id=actor_id,
         payload={"dropoff": d.dropoff_location})
    record(db, organization_id=org_id, actor_id=actor_id,
           action="delivery.created", resource="delivery", resource_id=str(d.id))
    uow.commit()
    db.refresh(d)
    return d


def list_deliveries(
    uow: UnitOfWork, org_id: uuid.UUID, status: str | None = None
) -> list[Delivery]:
    q = select(Delivery).where(Delivery.organization_id == org_id)
    if status:
        q = q.where(Delivery.status == status)
    return list(uow.session.scalars(q.order_by(Delivery.created_at.desc())))


def get_delivery(uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID) -> Delivery:
    d = uow.session.scalar(
        select(Delivery).where(
            Delivery.id == delivery_id, Delivery.organization_id == org_id
        )
    )
    if not d:
        raise NotFoundError("delivery not found")
    return d


def update_delivery(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    delivery_id: uuid.UUID, payload: DeliveryUpdate,
) -> Delivery:
    d = get_delivery(uow, org_id, delivery_id)
    if d.status in FINAL_STATES:
        raise ConflictError(f"cannot update delivery in status {d.status}")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="delivery.updated", resource="delivery", resource_id=str(d.id))
    uow.commit()
    uow.session.refresh(d)
    return d


def cancel_delivery(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    delivery_id: uuid.UUID, payload: DeliveryCancel,
) -> Delivery:
    db = uow.session
    d = get_delivery(uow, org_id, delivery_id)
    if d.status in FINAL_STATES:
        raise ConflictError(f"cannot cancel delivery in status {d.status}")

    prev = d.status
    d.status = "cancelled"
    d.failed_reason = payload.reason
    db.add(
        DeliveryStatusHistory(
            organization_id=org_id, delivery_id=d.id,
            from_status=prev, to_status="cancelled",
            actor_id=actor_id, note=payload.reason,
        )
    )
    _track(db, org_id, d.id, "cancelled", payload={"reason": payload.reason})
    emit(db, type="delivery.cancelled", aggregate_type="delivery", aggregate_id=d.id,
         organization_id=org_id, actor_id=actor_id, payload={"reason": payload.reason})
    record(db, organization_id=org_id, actor_id=actor_id,
           action="delivery.cancelled", resource="delivery", resource_id=str(d.id))
    uow.commit()
    db.refresh(d)
    return d


def reschedule_delivery(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    delivery_id: uuid.UUID, payload: DeliveryReschedule,
) -> Delivery:
    db = uow.session
    d = get_delivery(uow, org_id, delivery_id)
    if d.status not in {"pending", "failed", "rescheduled"}:
        raise ConflictError(f"cannot reschedule in status {d.status}")

    prev = d.status
    d.status = "rescheduled"
    d.scheduled_at = payload.scheduled_at
    d.failed_reason = None
    db.add(
        DeliveryStatusHistory(
            organization_id=org_id, delivery_id=d.id,
            from_status=prev, to_status="rescheduled", actor_id=actor_id,
        )
    )
    _track(db, org_id, d.id, "rescheduled",
           payload={"scheduled_at": payload.scheduled_at.isoformat()})
    record(db, organization_id=org_id, actor_id=actor_id,
           action="delivery.rescheduled", resource="delivery", resource_id=str(d.id))
    uow.commit()
    db.refresh(d)
    return d


def transition_delivery(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, delivery_id: uuid.UUID,
    payload: DeliveryStatusUpdate,
) -> Delivery:
    db = uow.session
    d = get_delivery(uow, org_id, delivery_id)
    current = d.status
    target = payload.status

    allowed = DELIVERY_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValidationError_(f"invalid transition: {current} -> {target}")

    if target == "delivered" and d.delivered_at is None:
        d.delivered_at = _now()
    if target == "failed":
        if not payload.failed_reason:
            raise ValidationError_("failed_reason is required when marking failed")
        d.failed_reason = payload.failed_reason

    d.status = target

    db.add(
        DeliveryStatusHistory(
            organization_id=org_id, delivery_id=d.id,
            from_status=current, to_status=target, actor_id=actor_id,
            lat=payload.lat, lng=payload.lng, note=payload.note,
        )
    )
    _track(db, org_id, d.id, target, lat=payload.lat, lng=payload.lng,
           payload={"from": current, "note": payload.note})
    emit(db, type=f"delivery.{target}", aggregate_type="delivery", aggregate_id=d.id,
         organization_id=org_id, actor_id=actor_id,
         payload={"from": current, "lat": payload.lat, "lng": payload.lng})
    record(db, organization_id=org_id, actor_id=actor_id,
           action=f"delivery.{target}", resource="delivery", resource_id=str(d.id))
    uow.commit()
    db.refresh(d)
    return d


def list_history(
    uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID
) -> list[DeliveryStatusHistory]:
    get_delivery(uow, org_id, delivery_id)
    return list(
        uow.session.scalars(
            select(DeliveryStatusHistory)
            .where(
                DeliveryStatusHistory.organization_id == org_id,
                DeliveryStatusHistory.delivery_id == delivery_id,
            )
            .order_by(DeliveryStatusHistory.created_at)
        )
    )


def list_my_deliveries(
    uow: UnitOfWork, org_id: uuid.UUID, user_id: uuid.UUID
) -> list[Delivery]:
    from app.modules.drivers.models import Driver

    db = uow.session
    driver = db.scalar(
        select(Driver).where(
            Driver.organization_id == org_id, Driver.user_id == user_id
        )
    )
    if not driver:
        return []
    return list(
        db.scalars(
            select(Delivery)
            .join(Assignment, Assignment.delivery_id == Delivery.id)
            .where(
                Delivery.organization_id == org_id,
                Assignment.driver_id == driver.id,
                Assignment.status.in_(["offered", "accepted"]),
            )
            .order_by(Delivery.created_at.desc())
        )
    )


def add_pod(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, delivery_id: uuid.UUID,
    payload: PODCreate,
) -> ProofOfDelivery:
    db = uow.session
    get_delivery(uow, org_id, delivery_id)
    pod = ProofOfDelivery(
        organization_id=org_id,
        delivery_id=delivery_id,
        kind=payload.kind,
        s3_key=payload.s3_key,
        signer_name=payload.signer_name,
        signature_s3_key=payload.signature_s3_key,
        lat=payload.lat,
        lng=payload.lng,
    )
    db.add(pod)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="pod.added", resource="proof_of_delivery", resource_id=str(pod.id))
    uow.commit()
    db.refresh(pod)
    return pod


def list_pods(
    uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID
) -> list[ProofOfDelivery]:
    get_delivery(uow, org_id, delivery_id)
    return list(
        uow.session.scalars(
            select(ProofOfDelivery)
            .where(
                ProofOfDelivery.organization_id == org_id,
                ProofOfDelivery.delivery_id == delivery_id,
            )
            .order_by(ProofOfDelivery.captured_at)
        )
    )