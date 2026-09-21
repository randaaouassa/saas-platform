import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.events.publisher import emit
from app.core.uow import UnitOfWork
from app.modules.inventory.models import StockReservation
from app.modules.inventory.schemas import ReservationCreate
from app.modules.inventory.service import release_reservation, reserve_stock
from app.modules.orders.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatusHistory,
)
from app.modules.orders.schemas import (
    CustomerCreate,
    CustomerUpdate,
    OrderCreate,
    OrderStatusUpdate,
)

ORDER_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"reserved", "cancelled"},
    "reserved": {"picking", "cancelled"},
    "picking": {"packed", "cancelled"},
    "packed": {"ready_for_dispatch", "cancelled"},
    "ready_for_dispatch": {"dispatched", "cancelled"},
    "dispatched": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
    "on_hold": {"confirmed", "cancelled"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_customer(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: CustomerCreate
) -> Customer:
    db = uow.session
    c = Customer(organization_id=org_id, **payload.model_dump())
    db.add(c)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="customer.created", resource="customer", resource_id=str(c.id))
    uow.commit()
    db.refresh(c)
    return c


def list_customers(uow: UnitOfWork, org_id: uuid.UUID) -> list[Customer]:
    return list(
        uow.session.scalars(
            select(Customer).where(Customer.organization_id == org_id).order_by(Customer.created_at)
        )
    )


def get_customer(uow: UnitOfWork, org_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    c = uow.session.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.organization_id == org_id)
    )
    if not c:
        raise NotFoundError("customer not found")
    return c


def update_customer(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, customer_id: uuid.UUID, payload: CustomerUpdate
) -> Customer:
    c = get_customer(uow, org_id, customer_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="customer.updated", resource="customer", resource_id=str(c.id))
    uow.commit()
    uow.session.refresh(c)
    return c


def create_order(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: OrderCreate
) -> Order:
    db = uow.session

    exists = db.scalar(
        select(Order).where(Order.organization_id == org_id, Order.number == payload.number)
    )
    if exists:
        raise ConflictError("order number already exists")

    get_customer(uow, org_id, payload.customer_id)

    order = Order(
        organization_id=org_id,
        customer_id=payload.customer_id,
        number=payload.number,
        status="draft",
        currency=payload.currency,
        notes=payload.notes,
    )
    db.add(order)
    uow.flush()

    total = Decimal("0")
    for item in payload.items:
        line_total = Decimal(item.quantity) * Decimal(item.unit_price)
        total += line_total
        db.add(
            OrderItem(
                organization_id=org_id,
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=line_total,
            )
        )
    order.total_amount = total

    db.add(
        OrderStatusHistory(
            organization_id=org_id, order_id=order.id,
            from_status=None, to_status="draft", actor_id=actor_id,
        )
    )
    emit(
        db, type="order.created", aggregate_type="order", aggregate_id=order.id,
        organization_id=org_id, actor_id=actor_id,
        payload={"number": order.number, "total": str(order.total_amount)},
    )
    record(db, organization_id=org_id, actor_id=actor_id,
           action="order.created", resource="order", resource_id=str(order.id))
    uow.commit()
    db.refresh(order)
    return order


def list_orders(uow: UnitOfWork, org_id: uuid.UUID, status: str | None = None) -> list[Order]:
    q = select(Order).where(Order.organization_id == org_id)
    if status:
        q = q.where(Order.status == status)
    return list(uow.session.scalars(q.order_by(Order.created_at.desc())))


def get_order(uow: UnitOfWork, org_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    o = uow.session.scalar(
        select(Order).where(Order.id == order_id, Order.organization_id == org_id)
    )
    if not o:
        raise NotFoundError("order not found")
    return o


def transition_order(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, order_id: uuid.UUID,
    payload: OrderStatusUpdate, warehouse_id: uuid.UUID | None = None,
) -> Order:
    db = uow.session
    order = get_order(uow, org_id, order_id)
    current = order.status
    target = payload.status

    allowed = ORDER_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValidationError_(f"invalid transition: {current} -> {target}")

    if target == "reserved":
        if not warehouse_id:
            raise ValidationError_("warehouse_id is required to reserve stock")
        for item in order.items:
            reserve_stock(
                uow, org_id, actor_id,
                ReservationCreate(
                    product_id=item.product_id,
                    warehouse_id=warehouse_id,
                    quantity=item.quantity,
                    ref_type="order",
                    ref_id=order.id,
                ),
            )

    if target == "cancelled":
        reservations = list(
            db.scalars(
                select(StockReservation).where(
                    StockReservation.organization_id == org_id,
                    StockReservation.ref_type == "order",
                    StockReservation.ref_id == order.id,
                    StockReservation.status == "active",
                )
            )
        )
        for r in reservations:
            release_reservation(uow, org_id, actor_id, r.id, consume=False)

    if target == "dispatched":
        reservations = list(
            db.scalars(
                select(StockReservation).where(
                    StockReservation.organization_id == org_id,
                    StockReservation.ref_type == "order",
                    StockReservation.ref_id == order.id,
                    StockReservation.status == "active",
                )
            )
        )
        for r in reservations:
            release_reservation(uow, org_id, actor_id, r.id, consume=True)

    order.status = target
    if target == "confirmed" and order.placed_at is None:
        order.placed_at = _now()

    db.add(
        OrderStatusHistory(
            organization_id=org_id, order_id=order.id,
            from_status=current, to_status=target,
            actor_id=actor_id, reason=payload.reason,
        )
    )
    emit(
        db, type=f"order.{target}", aggregate_type="order", aggregate_id=order.id,
        organization_id=org_id, actor_id=actor_id, payload={"from": current},
    )
    record(db, organization_id=org_id, actor_id=actor_id,
           action=f"order.{target}", resource="order", resource_id=str(order.id))
    uow.commit()
    db.refresh(order)
    return order


def list_history(
    uow: UnitOfWork, org_id: uuid.UUID, order_id: uuid.UUID
) -> list[OrderStatusHistory]:
    get_order(uow, org_id, order_id)
    return list(
        uow.session.scalars(
            select(OrderStatusHistory)
            .where(
                OrderStatusHistory.organization_id == org_id,
                OrderStatusHistory.order_id == order_id,
            )
            .order_by(OrderStatusHistory.created_at)
        )
    )