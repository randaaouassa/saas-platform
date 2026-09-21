import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.deliveries import service
from app.modules.deliveries.schemas import (
    DeliveryCreate,
    DeliveryOut,
    DeliveryStatusHistoryOut,
    DeliveryStatusUpdate,
    PODCreate,
    PODOut,
)
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

STAFF = require_roles("org_admin", "warehouse_manager", "dispatcher")


@router.post("", response_model=DeliveryOut, status_code=status.HTTP_201_CREATED)
def create_delivery(
    payload: DeliveryCreate,
    user: User = Depends(STAFF),
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveryOut:
    return DeliveryOut.model_validate(service.create_delivery(uow, user.organization_id, user.id, payload))


@router.get("", response_model=list[DeliveryOut])
def list_deliveries(
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DeliveryOut]:
    return [
        DeliveryOut.model_validate(d)
        for d in service.list_deliveries(uow, user.organization_id, status_filter)
    ]


@router.get("/{delivery_id}", response_model=DeliveryOut)
def get_delivery(
    delivery_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveryOut:
    return DeliveryOut.model_validate(service.get_delivery(uow, user.organization_id, delivery_id))


@router.post("/{delivery_id}/status", response_model=DeliveryOut)
def transition_delivery(
    delivery_id: uuid.UUID,
    payload: DeliveryStatusUpdate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveryOut:
    d = service.transition_delivery(uow, user.organization_id, user.id, delivery_id, payload)
    return DeliveryOut.model_validate(d)


@router.get("/{delivery_id}/history", response_model=list[DeliveryStatusHistoryOut])
def list_history(
    delivery_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DeliveryStatusHistoryOut]:
    return [
        DeliveryStatusHistoryOut.model_validate(h)
        for h in service.list_history(uow, user.organization_id, delivery_id)
    ]


@router.post("/{delivery_id}/pod", response_model=PODOut, status_code=status.HTTP_201_CREATED)
def add_pod(
    delivery_id: uuid.UUID,
    payload: PODCreate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PODOut:
    return PODOut.model_validate(
        service.add_pod(uow, user.organization_id, user.id, delivery_id, payload)
    )


@router.get("/{delivery_id}/pod", response_model=list[PODOut])
def list_pods(
    delivery_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[PODOut]:
    return [
        PODOut.model_validate(p)
        for p in service.list_pods(uow, user.organization_id, delivery_id)
    ]