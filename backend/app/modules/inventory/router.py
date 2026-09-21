import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.inventory import service
from app.modules.inventory.schemas import (
    AlertCreate,
    AlertOut,
    AlertUpdate,
    MovementOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ReservationCreate,
    ReservationOut,
    StockAdjust,
    StockOut,
    StockReceive,
    StockTransfer,
    TransferResult,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])

MANAGER = require_roles("org_admin", "warehouse_manager")
STAFF = require_roles("org_admin", "warehouse_manager", "warehouse_staff")


# ---------- Products ----------
@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductOut:
    return ProductOut.model_validate(
        service.create_product(uow, user.organization_id, user.id, payload)
    )


@router.get("/products", response_model=list[ProductOut])
def list_products(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[ProductOut]:
    return [
        ProductOut.model_validate(p)
        for p in service.list_products(uow, user.organization_id)
    ]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductOut:
    return ProductOut.model_validate(
        service.get_product(uow, user.organization_id, product_id)
    )


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductOut:
    return ProductOut.model_validate(
        service.update_product(uow, user.organization_id, user.id, product_id, payload)
    )


# ---------- Stock ----------
@router.post("/stock/receive", response_model=StockOut, status_code=status.HTTP_201_CREATED)
def receive_stock(
    payload: StockReceive,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> StockOut:
    s = service.receive_stock(uow, user.organization_id, user.id, payload)
    return StockOut(
        id=s.id, product_id=s.product_id, warehouse_id=s.warehouse_id,
        location_id=s.location_id, quantity=s.quantity,
        reserved_quantity=s.reserved_quantity,
        available=s.quantity - s.reserved_quantity,
    )


@router.post("/stock/adjust", response_model=StockOut)
def adjust_stock(
    payload: StockAdjust,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> StockOut:
    s = service.adjust_stock(uow, user.organization_id, user.id, payload)
    return StockOut(
        id=s.id, product_id=s.product_id, warehouse_id=s.warehouse_id,
        location_id=s.location_id, quantity=s.quantity,
        reserved_quantity=s.reserved_quantity,
        available=s.quantity - s.reserved_quantity,
    )


@router.post("/stock/transfer", response_model=TransferResult)
def transfer_stock(
    payload: StockTransfer,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> TransferResult:
    result = service.transfer_stock(
        uow, user.organization_id, user.id,
        payload.product_id, payload.from_warehouse_id,
        payload.to_warehouse_id, payload.quantity,
    )
    return TransferResult(**result)


@router.get("/stock", response_model=list[StockOut])
def list_stock(
    warehouse_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[StockOut]:
    return [
        StockOut(**row)
        for row in service.list_stock(uow, user.organization_id, warehouse_id)
    ]


# ---------- Reservations ----------
@router.post(
    "/reservations", response_model=ReservationOut, status_code=status.HTTP_201_CREATED
)
def create_reservation(
    payload: ReservationCreate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> ReservationOut:
    return ReservationOut.model_validate(
        service.reserve_stock(uow, user.organization_id, user.id, payload)
    )


@router.post("/reservations/{reservation_id}/release", response_model=ReservationOut)
def release_reservation(
    reservation_id: uuid.UUID,
    consume: bool = False,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> ReservationOut:
    return ReservationOut.model_validate(
        service.release_reservation(
            uow, user.organization_id, user.id, reservation_id, consume=consume
        )
    )


# ---------- Movements ----------
@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    product_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[MovementOut]:
    return [
        MovementOut.model_validate(m)
        for m in service.list_movements(uow, user.organization_id, product_id)
    ]


# ---------- Alerts ----------
@router.post("/alerts", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> AlertOut:
    return AlertOut.model_validate(
        service.create_alert(uow, user.organization_id, user.id, payload)
    )


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    only_triggered: bool = False,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[AlertOut]:
    return [
        AlertOut.model_validate(a)
        for a in service.list_alerts(uow, user.organization_id, only_triggered)
    ]


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> AlertOut:
    return AlertOut.model_validate(
        service.update_alert(
            uow, user.organization_id, user.id, alert_id, payload.threshold
        )
    )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: uuid.UUID,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> AlertOut:
    return AlertOut.model_validate(
        service.resolve_alert(uow, user.organization_id, user.id, alert_id)
    )


@router.post("/alerts/low-stock-scan", response_model=list[dict])
def low_stock_scan(
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> list[dict]:
    return service.low_stock_scan(uow, user.organization_id, user.id)