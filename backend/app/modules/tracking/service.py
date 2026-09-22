import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.uow import UnitOfWork
from app.modules.deliveries.models import Delivery, DeliveryStatusHistory
from app.modules.tracking.models import TrackingEvent


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_public_token(uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID) -> str:
    db = uow.session
    d = db.scalar(
        select(Delivery).where(Delivery.id == delivery_id, Delivery.organization_id == org_id)
    )
    if not d:
        raise ValueError("delivery not found")
    if not d.public_token:
        d.public_token = secrets.token_urlsafe(16)[:22]
        uow.commit()
    return d.public_token


def record_event(
    uow: UnitOfWork,
    org_id: uuid.UUID,
    delivery_id: uuid.UUID,
    event_type: str,
    lat: float | None = None,
    lng: float | None = None,
    payload: dict | None = None,
) -> TrackingEvent:
    db = uow.session
    e = TrackingEvent(
        organization_id=org_id,
        delivery_id=delivery_id,
        type=event_type,
        lat=lat,
        lng=lng,
        payload_json=payload or {},
    )
    db.add(e)
    uow.commit()
    db.refresh(e)
    return e


def list_events(uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID) -> list[TrackingEvent]:
    return list(
        uow.session.scalars(
            select(TrackingEvent)
            .where(
                TrackingEvent.organization_id == org_id,
                TrackingEvent.delivery_id == delivery_id,
            )
            .order_by(TrackingEvent.created_at)
        )
    )


def get_public_status(uow: UnitOfWork, token: str) -> dict | None:
    db = uow.session
    d = db.scalar(select(Delivery).where(Delivery.public_token == token))
    if not d:
        return None

    history = list(
        db.scalars(
            select(TrackingEvent)
            .where(TrackingEvent.delivery_id == d.id)
            .order_by(TrackingEvent.created_at)
        )
    )
    status_hist = list(
        db.scalars(
            select(DeliveryStatusHistory)
            .where(DeliveryStatusHistory.delivery_id == d.id)
            .order_by(DeliveryStatusHistory.created_at)
        )
    )

    events = [
        {
            "id": h.id,
            "delivery_id": h.delivery_id,
            "type": h.to_status,
            "lat": h.lat,
            "lng": h.lng,
            "payload_json": {"from": h.from_status, "note": h.note},
            "created_at": h.created_at,
        }
        for h in status_hist
    ]
    events += [
        {
            "id": e.id,
            "delivery_id": e.delivery_id,
            "type": e.type,
            "lat": e.lat,
            "lng": e.lng,
            "payload_json": e.payload_json,
            "created_at": e.created_at,
        }
        for e in history
    ]
    events.sort(key=lambda x: x["created_at"])

    return {
        "delivery_id": d.id,
        "status": d.status,
        "dropoff_location": d.dropoff_location,
        "dropoff_lat": d.dropoff_lat,
        "dropoff_lng": d.dropoff_lng,
        "scheduled_at": d.scheduled_at,
        "delivered_at": d.delivered_at,
        "history": events,
    }