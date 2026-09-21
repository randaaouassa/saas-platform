import uuid

from fastapi import APIRouter, Depends, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.notifications import service
from app.modules.notifications.schemas import (
    NotificationCreate,
    NotificationDeliveryOut,
    NotificationOut,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

MANAGER = require_roles("org_admin", "warehouse_manager", "dispatcher")


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    user: User = Depends(MANAGER),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationOut:
    return NotificationOut.model_validate(
        service.create_notification(uow, user.organization_id, user.id, payload)
    )


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    user_id: uuid.UUID | None = None,
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[NotificationOut]:
    return [
        NotificationOut.model_validate(n)
        for n in service.list_notifications(uow, user.organization_id, user_id, unread_only)
    ]


@router.get("/mine", response_model=list[NotificationOut])
def list_mine(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[NotificationOut]:
    return [
        NotificationOut.model_validate(n)
        for n in service.list_notifications(uow, user.organization_id, user.id, unread_only)
    ]


@router.post("/mine/read-all", response_model=dict)
def mark_all_read(
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> dict:
    count = service.mark_all_read(uow, user.organization_id, user.id)
    return {"marked": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationOut:
    return NotificationOut.model_validate(
        service.mark_read(uow, user.organization_id, user.id, notification_id)
    )


@router.get("/{notification_id}/deliveries", response_model=list[NotificationDeliveryOut])
def list_deliveries(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[NotificationDeliveryOut]:
    return [
        NotificationDeliveryOut.model_validate(d)
        for d in service.list_deliveries(uow, user.organization_id, notification_id)
    ]