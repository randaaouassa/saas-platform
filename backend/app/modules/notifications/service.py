import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import NotFoundError, ValidationError_
from app.core.uow import UnitOfWork
from app.modules.notifications.models import Notification, NotificationDelivery
from app.modules.notifications.schemas import CHANNELS, NotificationCreate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_notification(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: NotificationCreate
) -> Notification:
    if payload.channel not in CHANNELS:
        raise ValidationError_(f"invalid channel: {payload.channel}")

    db = uow.session
    n = Notification(
        organization_id=org_id,
        user_id=payload.user_id,
        customer_id=payload.customer_id,
        channel=payload.channel,
        template=payload.template,
        payload_json=payload.payload,
        status="queued",
    )
    db.add(n)
    uow.flush()

    if payload.channel == "inapp":
        n.status = "sent"
    else:
        db.add(
            NotificationDelivery(
                organization_id=org_id,
                notification_id=n.id,
                provider=payload.channel,
                status="pending",
            )
        )

    record(db, organization_id=org_id, actor_id=actor_id,
           action="notification.created", resource="notification", resource_id=str(n.id))
    uow.commit()
    db.refresh(n)
    return n


def list_notifications(
    uow: UnitOfWork, org_id: uuid.UUID, user_id: uuid.UUID | None = None, unread_only: bool = False
) -> list[Notification]:
    q = select(Notification).where(Notification.organization_id == org_id)
    if user_id:
        q = q.where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.read_at.is_(None))
    return list(uow.session.scalars(q.order_by(Notification.created_at.desc())))


def get_notification(uow: UnitOfWork, org_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    n = uow.session.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.organization_id == org_id
        )
    )
    if not n:
        raise NotFoundError("notification not found")
    return n


def mark_read(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification:
    n = get_notification(uow, org_id, notification_id)
    if n.read_at is None:
        n.read_at = _now()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="notification.read", resource="notification", resource_id=str(n.id))
    uow.commit()
    uow.session.refresh(n)
    return n


def mark_all_read(uow: UnitOfWork, org_id: uuid.UUID, user_id: uuid.UUID) -> int:
    db = uow.session
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.organization_id == org_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
    )
    now = _now()
    for r in rows:
        r.read_at = now
    uow.commit()
    return len(rows)


def list_deliveries(
    uow: UnitOfWork, org_id: uuid.UUID, notification_id: uuid.UUID
) -> list[NotificationDelivery]:
    get_notification(uow, org_id, notification_id)
    return list(
        uow.session.scalars(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.organization_id == org_id,
                NotificationDelivery.notification_id == notification_id,
            )
            .order_by(NotificationDelivery.created_at)
        )
    )


def mark_delivery_sent(
    uow: UnitOfWork, org_id: uuid.UUID, delivery_id: uuid.UUID,
    provider_msg_id: str | None = None, error: str | None = None,
) -> NotificationDelivery:
    db = uow.session
    d = db.scalar(
        select(NotificationDelivery).where(
            NotificationDelivery.id == delivery_id,
            NotificationDelivery.organization_id == org_id,
        )
    )
    if not d:
        raise NotFoundError("delivery not found")

    d.attempts += 1
    if error:
        d.status = "failed"
        d.error = error
    else:
        d.status = "sent"
        d.sent_at = _now()
        d.provider_msg_id = provider_msg_id

    n = db.get(Notification, d.notification_id)
    if n:
        n.status = d.status
    uow.commit()
    db.refresh(d)
    return d