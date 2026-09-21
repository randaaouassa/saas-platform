import time

import structlog
from fastapi import Request
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings

log = structlog.get_logger("rate_limit")


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


RULES: list[tuple[str, str, int, int]] = [
    ("/api/v1/auth/login", "POST", 10, 300),
    ("/api/v1/auth/register", "POST", 5, 3600),
    ("/api/v1/auth/refresh", "POST", 60, 60),
    ("/api/v1/auth/invitations", "POST", 20, 3600),
    ("/api/v1/", "*", 600, 60),
]

EXEMPT_PATHS = {"/health/live", "/health/ready", "/metrics"}


def _client_key(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth:
        return f"user:{auth[-32:]}"
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


def _match_rule(path: str, method: str) -> tuple[int, int] | None:
    for prefix, m, limit, window in RULES:
        if not path.startswith(prefix):
            continue
        if m != "*" and m != method:
            continue
        return limit, window
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        rule = _match_rule(request.url.path, request.method)
        if not rule:
            return await call_next(request)

        limit, window = rule
        now = int(time.time())
        bucket = now // window
        identity = _client_key(request)
        key = f"rl:{identity}:{request.url.path}:{bucket}"

        client = _redis()
        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, window)
        except Exception as e:
            log.warning("rate_limit_redis_error", error=str(e))
            return await call_next(request)

        remaining = max(0, limit - count)
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str((bucket + 1) * window),
        }

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "type": "about:blank#rate_limited",
                    "title": "Too many requests",
                    "status": 429,
                },
                headers={**headers, "Retry-After": str((bucket + 1) * window - now)},
                media_type="application/problem+json",
            )

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response