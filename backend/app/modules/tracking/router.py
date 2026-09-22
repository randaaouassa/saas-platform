import asyncio
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.deps import get_current_user
from app.modules.identity.models import User
from app.modules.tracking import service
from app.modules.tracking.pubsub import subscribe
from app.modules.tracking.schemas import PublicTrackingStatus, TrackingEventOut

log = structlog.get_logger("tracking.ws")

ws_router = APIRouter(tags=["tracking-ws"])
router = APIRouter(tags=["tracking"])
public_router = APIRouter(prefix="/public/track", tags=["public-tracking"])

ALLOWED_TOPICS = {"delivery", "driver", "dispatcher", "notification"}


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def _forward(pubsub, ws: WebSocket, stop: asyncio.Event) -> None:
    loop = asyncio.get_event_loop()
    try:
        while not stop.is_set():
            msg = await loop.run_in_executor(None, pubsub.get_message, True, 1.0)
            if not msg:
                continue
            if msg.get("type") != "message":
                continue
            await ws.send_text(msg["data"])
    except Exception as e:
        log.warning("ws_forward_error", error=str(e))


@ws_router.websocket("/ws/tracking")
async def ws_tracking(
    websocket: WebSocket,
    token: str = Query(...),
    topics: str = Query("delivery,driver,dispatcher,notification"),
) -> None:
    try:
        payload = _decode(token)
    except JWTError:
        await websocket.close(code=4401)
        return
    if payload.get("type") != "access":
        await websocket.close(code=4401)
        return

    org_id_raw = payload.get("org")
    if not org_id_raw:
        await websocket.close(code=4401)
        return
    try:
        org_id = uuid.UUID(org_id_raw)
    except ValueError:
        await websocket.close(code=4401)
        return

    requested = {t.strip() for t in topics.split(",") if t.strip()}
    allowed = sorted(requested & ALLOWED_TOPICS)
    if not allowed:
        await websocket.close(code=4400)
        return

    await websocket.accept()
    pubsub = subscribe(org_id, allowed)
    stop = asyncio.Event()
    task = asyncio.create_task(_forward(pubsub, websocket, stop))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        stop.set()
        task.cancel()
        try:
            pubsub.close()
        except Exception:
            pass


@router.get(
    "/tracking/deliveries/{delivery_id}/events",
    response_model=list[TrackingEventOut],
)
def list_events(
    delivery_id: uuid.UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[TrackingEventOut]:
    return [
        TrackingEventOut.model_validate(e)
        for e in service.list_events(uow, user.organization_id, delivery_id)
    ]


@public_router.get("/{token}", response_model=PublicTrackingStatus)
def public_status(token: str, uow: UnitOfWork = Depends(get_uow)) -> PublicTrackingStatus:
    data = service.get_public_status(uow, token)
    if not data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tracking not found")
    return PublicTrackingStatus(**data)