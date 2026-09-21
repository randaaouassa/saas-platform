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
    OrderCancel,
    OrderCreate,
    OrderImportRequest,
    OrderItemAdd,
    OrderStatusUpdate,
    OrderUpdate,
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


# ---------- Customer ----------
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
            select(Customer)
            .where(Customer.organization_id == org_id)
            .order_by(Customer.created_at)
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
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    customer_id: uuid.UUID, payload: CustomerUpdate,
) -> Customer:
    c = get_customer(uow, org_id, customer_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="customer.updated", resource="customer", resource_id=str(c.id))
    uow.commit()
    uow.session.refresh(c)
    return c


# ---------- Order helpers ----------
def _recalc_total(db, order: Order) -> None:
    total = Decimal("0")
    for item in order.items:
        total += Decimal(item.total_price)
    order.total_amount = total


def _add_item(db, org_id: uuid.UUID, order: Order, product_id: uuid.UUID,
              quantity: Decimal, unit_price: Decimal) -> OrderItem:
    line_total = Decimal(quantity) * Decimal(unit_price)
    item = OrderItem(
        organization_id=org_id,
        order_id=order.id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        total_price=line_total,
    )
    db.add(item)
    return item


# ---------- Order ----------
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

    for item in payload.items:
        _add_item(db, org_id, order, item.product_id, item.quantity, item.unit_price)
    uow.flush()
    db.refresh(order)
    _recalc_total(db, order)

    db.add(OrderStatusHistory(
        organization_id=org_id, order_id=order.id,
        from_status=None, to_status="draft", actor_id=actor_id,
    ))
    emit(db, type="order.created", aggregate_type="order", aggregate_id=order.id,
         organization_id=org_id, actor_id=actor_id,
         payload={"number": order.number, "total": str(order.total_amount)})
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


def update_order(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    order_id: uuid.UUID, payload: OrderUpdate,
) -> Order:
    o = get_order(uow, org_id, order_id)
    if o.status not in {"draft", "on_hold"}:
        raise ConflictError(f"cannot update order in status {o.status}")
    if payload.customer_id is not None:
        get_customer(uow, org_id, payload.customer_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="order.updated", resource="order", resource_id=str(o.id))
    uow.commit()
    uow.session.refresh(o)
    return o


def add_order_item(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    order_id: uuid.UUID, payload: OrderItemAdd,
) -> Order:
    db = uow.session
    o = get_order(uow, org_id, order_id)
    if o.status not in {"draft", "on_hold"}:
        raise ConflictError(f"cannot add items in status {o.status}")
    _add_item(db, org_id, o, payload.product_id, payload.quantity, payload.unit_price)
    uow.flush()
    db.refresh(o)
    _recalc_total(db, o)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="order.item_added", resource="order", resource_id=str(o.id))
    uow.commit()
    db.refresh(o)
    return o


def remove_order_item(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    order_id: uuid.UUID, item_id: uuid.UUID,
) -> Order:
    db = uow.session
    o = get_order(uow, org_id, order_id)
    if o.status not in {"draft", "on_hold"}:
        raise ConflictError(f"cannot remove items in status {o.status}")
    item = db.scalar(
        select(OrderItem).where(OrderItem.id == item_id, OrderItem.order_id == o.id)
    )
    if not item:
        raise NotFoundError("item not found")
    db.delete(item)
    uow.flush()
    db.refresh(o)
    _recalc_total(db, o)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="order.item_removed", resource="order", resource_id=str(o.id))
    uow.commit()
    db.refresh(o)
    return o


def cancel_order(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    order_id: uuid.UUID, payload: OrderCancel,
) -> Order:
    db = uow.session
    o = get_order(uow, org_id, order_id)
    if o.status in {"delivered", "cancelled"}:
        raise ConflictError(f"cannot cancel order in status {o.status}")

    reservations = list(
        db.scalars(
            select(StockReservation).where(
                StockReservation.organization_id == org_id,
                StockReservation.ref_type == "order",
                StockReservation.ref_id == o.id,
                StockReservation.status == "active",
            )
        )
    )
    for r in reservations:
        release_reservation(uow, org_id, actor_id, r.id, consume=False)

    prev = o.status
    o.status = "cancelled"
    db.add(OrderStatusHistory(
        organization_id=org_id, order_id=o.id,
        from_status=prev, to_status="cancelled",
        actor_id=actor_id, reason=payload.reason,
    ))
    emit(db, type="order.cancelled", aggregate_type="order", aggregate_id=o.id,
         organization_id=org_id, actor_id=actor_id, payload={"reason": payload.reason})
    record(db, organization_id=org_id, actor_id=actor_id,
           action="order.cancelled", resource="order", resource_id=str(o.id))
    uow.commit()
    db.refresh(o)
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

    db.add(OrderStatusHistory(
        organization_id=org_id, order_id=order.id,
        from_status=current, to_status=target,
        actor_id=actor_id, reason=payload.reason,
    ))
    emit(db, type=f"order.{target}", aggregate_type="order", aggregate_id=order.id,
         organization_id=org_id, actor_id=actor_id, payload={"from": current})
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


def import_orders(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: OrderImportRequest
) -> dict:
    db = uow.session
    created = 0
    errors: list[dict] = []

    for idx, row in enumerate(payload.rows):
        try:
            exists = db.scalar(
                select(Order).where(
                    Order.organization_id == org_id, Order.number == row.number
                )
            )
            if exists:
                errors.append({"row": idx, "error": f"order {row.number} exists"})
                continue

            customer = None
            if row.customer_email:
                customer = db.scalar(
                    select(Customer).where(
                        Customer.organization_id == org_id, Customer.email == row.customer_email
                    )
                )
            if not customer and row.customer_name:
                customer = db.scalar(
                    select(Customer).where(
                        Customer.organization_id == org_id, Customer.name == row.customer_name
                    )
                )
            if not customer:
                if not row.customer_name:
                    errors.append({"row": idx, "error": "customer_name or email required"})
                    continue
                customer = Customer(
                    organization_id=org_id,
                    name=row.customer_name,
                    email=row.customer_email,
                )
                db.add(customer)
                db.flush()

            order = Order(
                organization_id=org_id,
                customer_id=customer.id,
                number=row.number,
                status="draft",
                currency=row.currency,
            )
            db.add(order)
            db.flush()

            for it in row.items:
                _add_item(db, org_id, order, it.product_id, it.quantity, it.unit_price)
            uow.flush()
            db.refresh(order)
            _recalc_total(db, order)

            db.add(OrderStatusHistory(
                organization_id=org_id, order_id=order.id,
                from_status=None, to_status="draft", actor_id=actor_id,
            ))
            created += 1
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    record(db, organization_id=org_id, actor_id=actor_id,
           action="orders.imported", resource="order",
           metadata={"created": created, "errors": len(errors)})
    uow.commit()
    return {"created": created, "errors": errors}