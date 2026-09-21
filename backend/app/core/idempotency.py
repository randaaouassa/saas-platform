import json

import structlog
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

log = structlog.get_logger("idempotency")

IDEMPOTENCY_HEADER = "idempotency-key"
TTL_SECONDS = 60 * 60 * 24  # 24h
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
ENFORCED_PREFIXES = ("/api/v1/",)


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Ensures POST/PUT with Idempotency-Key header run once."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in SAFE_METHODS:
            return await call_next(request)

        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key:
            return await call_next(request)

        # only enforce under API prefix
        if not request.url.path.startswith(ENFORCED_PREFIXES):
            return await call_next(request)

        cache_key = f"idem:{key}"
        client = _redis()

        cached = client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return JSONResponse(
                    status_code=data["status"],
                    content=data["body"],
                    headers={"X-Idempotent-Replay": "true"},
                )
            except Exception:
                log.warning("idem_cache_decode_failed", key=key)

        # mark in-flight
        got_lock = client.set(f"{cache_key}:lock", "1", nx=True, ex=30)
        if not got_lock:
            return JSONResponse(
                status_code=409,
                content={
                    "type": "about:blank#idempotency_in_flight",
                    "title": "Request with this Idempotency-Key is in progress",
                    "status": 409,
                },
                media_type="application/problem+json",
            )

        try:
            response = await call_next(request)
        finally:
            client.delete(f"{cache_key}:lock")

        # cache only successful / client-error responses
        if response.status_code < 500:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            payload = {
                "status": response.status_code,
                "body": json.loads(body.decode() or "{}"),
            }
            client.set(cache_key, json.dumps(payload), ex=TTL_SECONDS)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response