import asyncio
import uuid

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.modules.tracking.pubsub import subscribe

log = structlog.get_logger("tracking.ws")

router = APIRouter(tags=["tracking"])

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


@router.websocket("/ws/tracking")
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
            # keepalive / ignore inbound
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