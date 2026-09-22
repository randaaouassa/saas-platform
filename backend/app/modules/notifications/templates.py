from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    code: str
    subject: str
    body: str
    default_channel: str = "inapp"


TEMPLATES: dict[str, Template] = {
    "order.created": Template(
        code="order.created",
        subject="Order {number} received",
        body="We received order {number} totaling {total}.",
        default_channel="inapp",
    ),
    "order.confirmed": Template(
        code="order.confirmed",
        subject="Order {number} confirmed",
        body="Order {number} has been confirmed.",
    ),
    "order.dispatched": Template(
        code="order.dispatched",
        subject="Order {number} dispatched",
        body="Order {number} is on the way.",
    ),
    "delivery.created": Template(
        code="delivery.created",
        subject="Delivery scheduled",
        body="A delivery to {dropoff} has been scheduled.",
    ),
    "delivery.assigned": Template(
        code="delivery.assigned",
        subject="Driver assigned",
        body="A driver has been assigned to your delivery.",
        default_channel="push",
    ),
    "delivery.delivered": Template(
        code="delivery.delivered",
        subject="Delivery completed",
        body="Your delivery has been completed.",
    ),
    "delivery.failed": Template(
        code="delivery.failed",
        subject="Delivery failed",
        body="Delivery could not be completed.",
    ),
    "user.invited": Template(
        code="user.invited",
        subject="You're invited",
        body="You've been invited to join {org}.",
        default_channel="email",
    ),
    "stock.low": Template(
        code="stock.low",
        subject="Low stock alert",
        body="Low stock for product {product_id} at warehouse {warehouse_id}.",
    ),
}


def render(code: str, payload: dict) -> tuple[str, str, str]:
    tpl = TEMPLATES.get(code)
    if not tpl:
        return code, code, "inapp"
    try:
        subject = tpl.subject.format(**payload)
    except KeyError:
        subject = tpl.subject
    try:
        body = tpl.body.format(**payload)
    except KeyError:
        body = tpl.body
    return subject, body, tpl.default_channel