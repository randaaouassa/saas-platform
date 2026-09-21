import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select

from app.core.uow import UnitOfWork
from app.modules.analytics.models import (
    FactDeliveriesDaily,
    FactDriverDaily,
    FactInventoryDaily,
    FactOrdersDaily,
)
from app.modules.deliveries.models import Delivery
from app.modules.drivers.models import Driver
from app.modules.inventory.models import Stock, StockAlert
from app.modules.orders.models import Order


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def _upsert_orders(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> int:
    db = uow.session
    start, end = _day_bounds(d)
    orders_count = db.scalar(
        select(func.count(Order.id)).where(
            Order.organization_id == org_id,
            Order.created_at >= start,
            Order.created_at < end,
        )
    ) or 0
    delivered_count = db.scalar(
        select(func.count(Order.id)).where(
            Order.organization_id == org_id,
            Order.status == "delivered",
            Order.updated_at >= start,
            Order.updated_at < end,
        )
    ) or 0
    cancelled_count = db.scalar(
        select(func.count(Order.id)).where(
            Order.organization_id == org_id,
            Order.status == "cancelled",
            Order.updated_at >= start,
            Order.updated_at < end,
        )
    ) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.organization_id == org_id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.status != "cancelled",
        )
    ) or 0

    row = db.scalar(
        select(FactOrdersDaily).where(
            FactOrdersDaily.organization_id == org_id, FactOrdersDaily.date == d
        )
    )
    if not row:
        row = FactOrdersDaily(organization_id=org_id, date=d)
        db.add(row)
    row.orders_count = orders_count
    row.delivered_count = delivered_count
    row.cancelled_count = cancelled_count
    row.revenue = revenue
    return 1


def _upsert_deliveries(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> int:
    db = uow.session
    start, end = _day_bounds(d)
    total = db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.organization_id == org_id,
            Delivery.created_at >= start,
            Delivery.created_at < end,
        )
    ) or 0
    delivered = db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.organization_id == org_id,
            Delivery.status == "delivered",
            Delivery.updated_at >= start,
            Delivery.updated_at < end,
        )
    ) or 0
    failed = db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.organization_id == org_id,
            Delivery.status == "failed",
            Delivery.updated_at >= start,
            Delivery.updated_at < end,
        )
    ) or 0

    row = db.scalar(
        select(FactDeliveriesDaily).where(
            FactDeliveriesDaily.organization_id == org_id, FactDeliveriesDaily.date == d
        )
    )
    if not row:
        row = FactDeliveriesDaily(organization_id=org_id, date=d)
        db.add(row)
    row.deliveries_count = total
    row.delivered_count = delivered
    row.failed_count = failed
    row.avg_duration_s = None
    return 1


def _upsert_drivers(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> int:
    db = uow.session
    start, end = _day_bounds(d)
    drivers = list(db.scalars(select(Driver).where(Driver.organization_id == org_id)))
    rows = 0
    for drv in drivers:
        total = db.scalar(
            select(func.count(Delivery.id)).where(
                Delivery.organization_id == org_id,
                Delivery.created_at >= start,
                Delivery.created_at < end,
            )
        ) or 0
        delivered = db.scalar(
            select(func.count(Delivery.id)).where(
                Delivery.organization_id == org_id,
                Delivery.status == "delivered",
                Delivery.updated_at >= start,
                Delivery.updated_at < end,
            )
        ) or 0
        row = db.scalar(
            select(FactDriverDaily).where(
                FactDriverDaily.organization_id == org_id,
                FactDriverDaily.date == d,
                FactDriverDaily.driver_id == drv.id,
            )
        )
        if not row:
            row = FactDriverDaily(organization_id=org_id, date=d, driver_id=drv.id)
            db.add(row)
        row.deliveries_count = total
        row.delivered_count = delivered
        row.distance_m = 0
        rows += 1
    return rows


def _upsert_inventory(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> int:
    db = uow.session
    stocks = list(db.scalars(select(Stock).where(Stock.organization_id == org_id)))
    alerts = {
        (a.product_id, a.warehouse_id): a
        for a in db.scalars(
            select(StockAlert).where(
                StockAlert.organization_id == org_id, StockAlert.resolved_at.is_(None)
            )
        )
    }
    rows = 0
    for s in stocks:
        alert = alerts.get((s.product_id, s.warehouse_id))
        low = bool(alert and (s.quantity - s.reserved_quantity) <= alert.threshold)
        row = db.scalar(
            select(FactInventoryDaily).where(
                FactInventoryDaily.organization_id == org_id,
                FactInventoryDaily.date == d,
                FactInventoryDaily.product_id == s.product_id,
                FactInventoryDaily.warehouse_id == s.warehouse_id,
            )
        )
        if not row:
            row = FactInventoryDaily(
                organization_id=org_id, date=d,
                product_id=s.product_id, warehouse_id=s.warehouse_id,
            )
            db.add(row)
        row.on_hand = s.quantity
        row.reserved = s.reserved_quantity
        row.low_stock_flag = low
        rows += 1
    return rows


def rebuild_day(
    uow: UnitOfWork, org_id: uuid.UUID, d: date
) -> dict:
    o = _upsert_orders(uow, org_id, d)
    dl = _upsert_deliveries(uow, org_id, d)
    dr = _upsert_drivers(uow, org_id, d)
    inv = _upsert_inventory(uow, org_id, d)
    uow.commit()
    return {"date": d, "orders_rows": o, "deliveries_rows": dl,
            "driver_rows": dr, "inventory_rows": inv}


def get_orders_day(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> FactOrdersDaily | None:
    return uow.session.scalar(
        select(FactOrdersDaily).where(
            FactOrdersDaily.organization_id == org_id, FactOrdersDaily.date == d
        )
    )


def get_deliveries_day(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> FactDeliveriesDaily | None:
    return uow.session.scalar(
        select(FactDeliveriesDaily).where(
            FactDeliveriesDaily.organization_id == org_id, FactDeliveriesDaily.date == d
        )
    )


def list_drivers_day(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> list[FactDriverDaily]:
    return list(
        uow.session.scalars(
            select(FactDriverDaily)
            .where(FactDriverDaily.organization_id == org_id, FactDriverDaily.date == d)
            .order_by(FactDriverDaily.deliveries_count.desc())
        )
    )


def list_inventory_day(uow: UnitOfWork, org_id: uuid.UUID, d: date) -> list[FactInventoryDaily]:
    return list(
        uow.session.scalars(
            select(FactInventoryDaily)
            .where(FactInventoryDaily.organization_id == org_id, FactInventoryDaily.date == d)
            .order_by(FactInventoryDaily.low_stock_flag.desc())
        )
    )