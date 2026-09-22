from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.core.uow import UnitOfWork, get_uow
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    AvgDeliveryTimeResponse,
    DeliveriesSummary,
    DriverSummary,
    InventorySummary,
    OrdersSummary,
    OverviewResponse,
    RangeDeliveriesItem,
    RangeOrdersItem,
    RangeResponse,
    RebuildResponse,
)
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

MANAGER = require_roles("org_admin", "warehouse_manager", "dispatcher")


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild(
    day: date,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> RebuildResponse:
    result = service.rebuild_day(uow, user.organization_id, day)
    return RebuildResponse(**result)


@router.get("/orders", response_model=OrdersSummary | None)
def orders_day(
    day: date,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrdersSummary | None:
    row = service.get_orders_day(uow, user.organization_id, day)
    if not row:
        return None
    return OrdersSummary(
        date=row.date, orders_count=row.orders_count,
        delivered_count=row.delivered_count, cancelled_count=row.cancelled_count,
        revenue=float(row.revenue),
    )


@router.get("/deliveries", response_model=DeliveriesSummary | None)
def deliveries_day(
    day: date,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveriesSummary | None:
    row = service.get_deliveries_day(uow, user.organization_id, day)
    if not row:
        return None
    total = row.delivered_count + row.failed_count
    rate = (row.delivered_count / total) if total else 0.0
    return DeliveriesSummary(
        date=row.date,
        deliveries_count=row.deliveries_count,
        delivered_count=row.delivered_count,
        failed_count=row.failed_count,
        success_rate=round(rate, 4),
        avg_duration_s=float(row.avg_duration_s) if row.avg_duration_s else None,
    )


@router.get("/drivers", response_model=list[DriverSummary])
def drivers_day(
    day: date,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DriverSummary]:
    rows = service.list_drivers_day(uow, user.organization_id, day)
    return [
        DriverSummary(
            driver_id=str(r.driver_id),
            deliveries_count=r.deliveries_count,
            delivered_count=r.delivered_count,
            distance_m=float(r.distance_m),
        )
        for r in rows
    ]


@router.get("/inventory", response_model=list[InventorySummary])
def inventory_day(
    day: date,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[InventorySummary]:
    rows = service.list_inventory_day(uow, user.organization_id, day)
    return [
        InventorySummary(
            product_id=str(r.product_id),
            warehouse_id=str(r.warehouse_id),
            on_hand=float(r.on_hand),
            reserved=float(r.reserved),
            low_stock=r.low_stock_flag,
        )
        for r in rows
    ]


@router.get("/overview", response_model=OverviewResponse)
def overview(
    day: date,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OverviewResponse:
    o = service.get_orders_day(uow, user.organization_id, day)
    d = service.get_deliveries_day(uow, user.organization_id, day)
    drs = service.list_drivers_day(uow, user.organization_id, day)
    inv = service.list_inventory_day(uow, user.organization_id, day)

    orders = (
        OrdersSummary(
            date=o.date, orders_count=o.orders_count,
            delivered_count=o.delivered_count, cancelled_count=o.cancelled_count,
            revenue=float(o.revenue),
        ) if o else None
    )
    deliveries = None
    if d:
        total = d.delivered_count + d.failed_count
        rate = (d.delivered_count / total) if total else 0.0
        deliveries = DeliveriesSummary(
            date=d.date, deliveries_count=d.deliveries_count,
            delivered_count=d.delivered_count, failed_count=d.failed_count,
            success_rate=round(rate, 4),
            avg_duration_s=float(d.avg_duration_s) if d.avg_duration_s else None,
        )

    return OverviewResponse(
        orders=orders,
        deliveries=deliveries,
        drivers=[
            DriverSummary(
                driver_id=str(r.driver_id),
                deliveries_count=r.deliveries_count,
                delivered_count=r.delivered_count,
                distance_m=float(r.distance_m),
            )
            for r in drs
        ],
        inventory=[
            InventorySummary(
                product_id=str(r.product_id),
                warehouse_id=str(r.warehouse_id),
                on_hand=float(r.on_hand),
                reserved=float(r.reserved),
                low_stock=r.low_stock_flag,
            )
            for r in inv
        ],
    )


@router.get("/range", response_model=RangeResponse)
def range_summary(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RangeResponse:
    data = service.range_summary(uow, user.organization_id, from_date, to_date)
    return RangeResponse(
        from_date=data["from_date"],
        to_date=data["to_date"],
        orders=[RangeOrdersItem(**r) for r in data["orders"]],
        deliveries=[RangeDeliveriesItem(**r) for r in data["deliveries"]],
        total_revenue=data["total_revenue"],
        total_orders=data["total_orders"],
        total_deliveries=data["total_deliveries"],
        total_delivered=data["total_delivered"],
        total_failed=data["total_failed"],
        avg_delivery_time_s=data["avg_delivery_time_s"],
        top_products=data["top_products"],
    )


@router.get("/avg-delivery-time", response_model=AvgDeliveryTimeResponse)
def avg_time(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> AvgDeliveryTimeResponse:
    return AvgDeliveryTimeResponse(
        **service.avg_delivery_time(uow, user.organization_id, from_date, to_date)
    )


@router.get("/export/orders.csv", response_class=PlainTextResponse)
def export_orders(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> PlainTextResponse:
    csv_data = service.export_orders_csv(uow, user.organization_id, from_date, to_date)
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/export/deliveries.csv", response_class=PlainTextResponse)
def export_deliveries(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> PlainTextResponse:
    csv_data = service.export_deliveries_csv(uow, user.organization_id, from_date, to_date)
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=deliveries.csv"},
    )