import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.orders import service
from app.modules.orders.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    OrderCancel,
    OrderCreate,
    OrderImportRequest,
    OrderImportResult,
    OrderItemAdd,
    OrderOut,
    OrderStatusHistoryOut,
    OrderStatusUpdate,
    OrderUpdate,
)

router = APIRouter(prefix="/orders", tags=["orders"])
customers_router = APIRouter(prefix="/customers", tags=["customers"])

MANAGER = require_roles("org_admin", "warehouse_manager")
STAFF = require_roles("org_admin", "warehouse_manager", "warehouse_staff")


# ---------- Customers ----------
@customers_router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> CustomerOut:
    return CustomerOut.model_validate(
        service.create_customer(uow, user.organization_id, user.id, payload)
    )


@customers_router.get("", response_model=list[CustomerOut])
def list_customers(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[CustomerOut]:
    return [
        CustomerOut.model_validate(c)
        for c in service.list_customers(uow, user.organization_id)
    ]


@customers_router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> CustomerOut:
    return CustomerOut.model_validate(
        service.get_customer(uow, user.organization_id, customer_id)
    )


@customers_router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> CustomerOut:
    return CustomerOut.model_validate(
        service.update_customer(uow, user.organization_id, user.id, customer_id, payload)
    )


# ---------- Orders ----------
@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.create_order(uow, user.organization_id, user.id, payload)
    )


@router.post("/import", response_model=OrderImportResult)
def import_orders(
    payload: OrderImportRequest,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderImportResult:
    result = service.import_orders(uow, user.organization_id, user.id, payload)
    return OrderImportResult(**result)


@router.get("", response_model=list[OrderOut])
def list_orders(
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[OrderOut]:
    return [
        OrderOut.model_validate(o)
        for o in service.list_orders(uow, user.organization_id, status_filter)
    ]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.get_order(uow, user.organization_id, order_id)
    )


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.update_order(uow, user.organization_id, user.id, order_id, payload)
    )


@router.post("/{order_id}/items", response_model=OrderOut)
def add_order_item(
    order_id: uuid.UUID,
    payload: OrderItemAdd,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.add_order_item(uow, user.organization_id, user.id, order_id, payload)
    )


@router.delete("/{order_id}/items/{item_id}", response_model=OrderOut)
def remove_order_item(
    order_id: uuid.UUID,
    item_id: uuid.UUID,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.remove_order_item(uow, user.organization_id, user.id, order_id, item_id)
    )


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: uuid.UUID,
    payload: OrderCancel,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.cancel_order(uow, user.organization_id, user.id, order_id, payload)
    )


@router.post("/{order_id}/status", response_model=OrderOut)
def transition_order(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    warehouse_id: uuid.UUID | None = None,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> OrderOut:
    return OrderOut.model_validate(
        service.transition_order(
            uow, user.organization_id, user.id, order_id, payload, warehouse_id
        )
    )


@router.get("/{order_id}/history", response_model=list[OrderStatusHistoryOut])
def list_history(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[OrderStatusHistoryOut]:
    return [
        OrderStatusHistoryOut.model_validate(h)
        for h in service.list_history(uow, user.organization_id, order_id)
    ]