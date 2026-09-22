import structlog
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification
from app.modules.notifications.providers import dispatch
from app.modules.notifications.templates import render

log = structlog.get_logger("events.consumer")

# event type → notification template code (1:1 here)
NOTIFY_EVENTS = {
    "order.created",
    "order.confirmed",
    "order.dispatched",
    "delivery.created",
    "delivery.assigned",
    "delivery.delivered",
    "delivery.failed",
}


def handle_event(db: Session, event) -> None:
    """Convert a domain event into an in-app notification + optional outbound."""
    if event.type not in NOTIFY_EVENTS:
        return
    if not event.organization_id:
        return

    subject, body, channel = render(event.type, event.payload or {})

    n = Notification(
        organization_id=event.organization_id,
        user_id=None,
        customer_id=None,
        channel=channel,
        template=subject,
        payload_json={"body": body, **event.payload},
        status="queued",
    )
    db.add(n)
    db.flush()

    if channel == "inapp":
        n.status = "sent"
    else:
        try:
            result = dispatch(channel, None, subject, body)
            n.status = "sent"
            log.info("auto_notified", event=event.type, channel=channel,
                     msg_id=result.get("msg_id"))
        except Exception as e:
            n.status = "failed"
            log.warning("auto_notify_failed", event=event.type, error=str(e))