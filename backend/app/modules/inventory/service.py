import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.uow import UnitOfWork
from app.modules.inventory.models import (
    Product,
    Stock,
    StockAlert,
    StockMovement,
    StockReservation,
)
from app.modules.inventory.schemas import (
    AlertCreate,
    ProductCreate,
    ProductUpdate,
    ReservationCreate,
    StockAdjust,
    StockReceive,
)

MOVEMENT_TYPES = {
    "receipt",
    "transfer_out",
    "transfer_in",
    "adjustment_+",
    "adjustment_-",
    "reservation",
    "release",
    "pick",
    "pack",
    "ship",
    "return",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- Product ----------
def create_product(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: ProductCreate) -> Product:
    db = uow.session
    exists = db.scalar(select(Product).where(Product.organization_id == org_id, Product.sku == payload.sku))
    if exists:
        raise ConflictError("sku already exists")

    p = Product(organization_id=org_id, **payload.model_dump())
    db.add(p)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="product.created", resource="product", resource_id=str(p.id))
    uow.commit()
    db.refresh(p)
    return p


def list_products(uow: UnitOfWork, org_id: uuid.UUID) -> list[Product]:
    return list(
        uow.session.scalars(
            select(Product).where(Product.organization_id == org_id).order_by(Product.created_at)
        )
    )


def get_product(uow: UnitOfWork, org_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    p = uow.session.scalar(
        select(Product).where(Product.id == product_id, Product.organization_id == org_id)
    )
    if not p:
        raise NotFoundError("product not found")
    return p


def update_product(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, product_id: uuid.UUID, payload: ProductUpdate
) -> Product:
    p = get_product(uow, org_id, product_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="product.updated", resource="product", resource_id=str(p.id))
    uow.commit()
    uow.session.refresh(p)
    return p


# ---------- Internal helpers ----------
def _get_or_create_stock(
    db: Session, org_id: uuid.UUID, product_id: uuid.UUID, warehouse_id: uuid.UUID, location_id: uuid.UUID | None
) -> Stock:
    q = select(Stock).where(
        Stock.organization_id == org_id,
        Stock.product_id == product_id,
        Stock.warehouse_id == warehouse_id,
        Stock.location_id.is_(None) if location_id is None else Stock.location_id == location_id,
    )
    s = db.scalar(q)
    if not s:
        s = Stock(
            organization_id=org_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity=Decimal("0"),
            reserved_quantity=Decimal("0"),
        )
        db.add(s)
        db.flush()
    return s


def _log_movement(
    db: Session,
    org_id: uuid.UUID,
    *,
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    location_id: uuid.UUID | None,
    type: str,
    quantity: Decimal,
    actor_id: uuid.UUID | None,
    ref_type: str | None = None,
    ref_id: uuid.UUID | None = None,
) -> StockMovement:
    if type not in MOVEMENT_TYPES:
        raise ValidationError_(f"invalid movement type: {type}")
    m = StockMovement(
        organization_id=org_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        location_id=location_id,
        type=type,
        quantity=quantity,
        ref_type=ref_type,
        ref_id=ref_id,
        actor_id=actor_id,
    )
    db.add(m)
    return m


def _check_alerts(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, warehouse_id: uuid.UUID) -> None:
    alert = db.scalar(
        select(StockAlert).where(
            StockAlert.organization_id == org_id,
            StockAlert.product_id == product_id,
            StockAlert.warehouse_id == warehouse_id,
            StockAlert.resolved_at.is_(None),
        )
    )
    if not alert:
        return
    stock = db.scalar(
        select(Stock).where(
            Stock.organization_id == org_id,
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id,
        )
    )
    on_hand = stock.quantity if stock else Decimal("0")
    if on_hand <= alert.threshold and alert.triggered_at is None:
        alert.triggered_at = _now()
    elif on_hand > alert.threshold and alert.triggered_at is not None:
        alert.resolved_at = _now()


# ---------- Stock ----------
def receive_stock(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: StockReceive) -> Stock:
    db = uow.session
    get_product(uow, org_id, payload.product_id)
    s = _get_or_create_stock(db, org_id, payload.product_id, payload.warehouse_id, payload.location_id)
    s.quantity = s.quantity + payload.quantity
    _log_movement(
        db, org_id,
        product_id=payload.product_id, warehouse_id=payload.warehouse_id,
        location_id=payload.location_id, type="receipt",
        quantity=payload.quantity, actor_id=actor_id,
    )
    _check_alerts(db, org_id, payload.product_id, payload.warehouse_id)
    uow.commit()
    db.refresh(s)
    return s


def adjust_stock(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: StockAdjust) -> Stock:
    db = uow.session
    get_product(uow, org_id, payload.product_id)
    if payload.quantity == 0:
        raise ValidationError_("quantity must be non-zero")
    s = _get_or_create_stock(db, org_id, payload.product_id, payload.warehouse_id, payload.location_id)
    new_qty = s.quantity + payload.quantity
    if new_qty < 0:
        raise ValidationError_("adjustment would make stock negative")
    s.quantity = new_qty
    mtype = "adjustment_+" if payload.quantity > 0 else "adjustment_-"
    _log_movement(
        db, org_id,
        product_id=payload.product_id, warehouse_id=payload.warehouse_id,
        location_id=payload.location_id, type=mtype,
        quantity=payload.quantity, actor_id=actor_id,
    )
    _check_alerts(db, org_id, payload.product_id, payload.warehouse_id)
    uow.commit()
    db.refresh(s)
    return s


def list_stock(uow: UnitOfWork, org_id: uuid.UUID, warehouse_id: uuid.UUID | None = None) -> list[dict]:
    q = select(Stock).where(Stock.organization_id == org_id)
    if warehouse_id:
        q = q.where(Stock.warehouse_id == warehouse_id)
    rows = list(uow.session.scalars(q.order_by(Stock.created_at)))
    return [
        {
            "id": s.id,
            "product_id": s.product_id,
            "warehouse_id": s.warehouse_id,
            "location_id": s.location_id,
            "quantity": s.quantity,
            "reserved_quantity": s.reserved_quantity,
            "available": s.quantity - s.reserved_quantity,
        }
        for s in rows
    ]


# ---------- Reservation ----------
def reserve_stock(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: ReservationCreate
) -> StockReservation:
    db = uow.session
    get_product(uow, org_id, payload.product_id)
    s = _get_or_create_stock(db, org_id, payload.product_id, payload.warehouse_id, None)
    available = s.quantity - s.reserved_quantity
    if available < payload.quantity:
        raise ConflictError("insufficient available stock")

    s.reserved_quantity = s.reserved_quantity + payload.quantity
    r = StockReservation(
        organization_id=org_id,
        product_id=payload.product_id,
        warehouse_id=payload.warehouse_id,
        quantity=payload.quantity,
        ref_type=payload.ref_type,
        ref_id=payload.ref_id,
        status="active",
        expires_at=payload.expires_at,
    )
    db.add(r)
    _log_movement(
        db, org_id,
        product_id=payload.product_id, warehouse_id=payload.warehouse_id,
        location_id=None, type="reservation",
        quantity=payload.quantity, actor_id=actor_id,
        ref_type=payload.ref_type, ref_id=payload.ref_id,
    )
    uow.commit()
    db.refresh(r)
    return r


def release_reservation(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, reservation_id: uuid.UUID, consume: bool = False
) -> StockReservation:
    db = uow.session
    r = db.scalar(
        select(StockReservation).where(
            StockReservation.id == reservation_id, StockReservation.organization_id == org_id
        )
    )
    if not r:
        raise NotFoundError("reservation not found")
    if r.status != "active":
        raise ConflictError(f"reservation is {r.status}")

    s = _get_or_create_stock(db, org_id, r.product_id, r.warehouse_id, None)
    s.reserved_quantity = s.reserved_quantity - r.quantity
    if consume:
        s.quantity = s.quantity - r.quantity
        r.status = "consumed"
        mtype = "ship"
    else:
        r.status = "released"
        mtype = "release"

    _log_movement(
        db, org_id,
        product_id=r.product_id, warehouse_id=r.warehouse_id,
        location_id=None, type=mtype,
        quantity=r.quantity, actor_id=actor_id,
        ref_type=r.ref_type, ref_id=r.ref_id,
    )
    _check_alerts(db, org_id, r.product_id, r.warehouse_id)
    uow.commit()
    db.refresh(r)
    return r


# ---------- Movement history ----------
def list_movements(
    uow: UnitOfWork, org_id: uuid.UUID, product_id: uuid.UUID | None = None
) -> list[StockMovement]:
    q = select(StockMovement).where(StockMovement.organization_id == org_id)
    if product_id:
        q = q.where(StockMovement.product_id == product_id)
    return list(uow.session.scalars(q.order_by(StockMovement.created_at.desc())))


# ---------- Alerts ----------
def create_alert(uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, payload: AlertCreate) -> StockAlert:
    db = uow.session
    get_product(uow, org_id, payload.product_id)
    a = StockAlert(
        organization_id=org_id,
        product_id=payload.product_id,
        warehouse_id=payload.warehouse_id,
        threshold=payload.threshold,
    )
    db.add(a)
    uow.flush()
    record(db, organization_id=org_id, actor_id=actor_id,
           action="stock_alert.created", resource="stock_alert", resource_id=str(a.id))
    uow.commit()
    db.refresh(a)
    return a


def list_alerts(uow: UnitOfWork, org_id: uuid.UUID, only_triggered: bool = False) -> list[StockAlert]:
    q = select(StockAlert).where(StockAlert.organization_id == org_id)
    if only_triggered:
        q = q.where(StockAlert.triggered_at.is_not(None), StockAlert.resolved_at.is_(None))
    return list(uow.session.scalars(q.order_by(StockAlert.created_at.desc())))