import uuid

from sqlalchemy import func, select

from app.core.audit import record
from app.core.errors import NotFoundError
from app.core.uow import UnitOfWork
from app.modules.deliveries.models import Delivery
from app.modules.drivers.models import Driver
from app.modules.identity.models import Organization, User
from app.modules.inventory.models import Product
from app.modules.orders.models import Order
from app.modules.warehouse.models import Warehouse


def _count(db, model, *where) -> int:
    q = select(func.count(model.id))
    if where:
        q = q.where(*where)
    return db.scalar(q) or 0


def system_stats(uow: UnitOfWork) -> dict:
    db = uow.session
    return {
        "organizations": _count(db, Organization),
        "users": _count(db, User),
        "warehouses": _count(db, Warehouse),
        "products": _count(db, Product),
        "orders": _count(db, Order),
        "deliveries": _count(db, Delivery),
        "drivers": _count(db, Driver),
        "active_orgs": _count(db, Organization, Organization.status == "active"),
        "suspended_orgs": _count(db, Organization, Organization.status == "suspended"),
    }


def list_orgs(uow: UnitOfWork) -> list[dict]:
    db = uow.session
    orgs = list(db.scalars(select(Organization).order_by(Organization.created_at.desc())))
    out = []
    for o in orgs:
        users_count = db.scalar(
            select(func.count(User.id)).where(User.organization_id == o.id)
        ) or 0
        out.append(
            {
                "id": o.id,
                "name": o.name,
                "slug": o.slug,
                "plan": o.plan,
                "status": o.status,
                "users_count": users_count,
                "created_at": o.created_at,
            }
        )
    return out


def update_org_status(
    uow: UnitOfWork, actor_id: uuid.UUID, org_id: uuid.UUID, status: str
) -> Organization:
    db = uow.session
    org = db.get(Organization, org_id)
    if not org:
        raise NotFoundError("organization not found")
    prev = org.status
    org.status = status
    record(db, organization_id=org.id, actor_id=actor_id,
           action="org.status_changed", resource="organization",
           resource_id=str(org.id), metadata={"from": prev, "to": status})
    uow.commit()
    db.refresh(org)
    return org