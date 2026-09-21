import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration (s)",
    ["method", "path"],
)

domain_events_unpublished_total = Gauge(
    "domain_events_unpublished_total",
    "Number of unpublished domain events",
)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        if path in {"/metrics", "/health/live", "/health/ready"}:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            route = request.scope.get("route")
            label_path = getattr(route, "path", path)
            http_requests_total.labels(method=method, path=label_path, status=str(status_code)).inc()
            http_request_duration_seconds.labels(method=method, path=label_path).observe(duration)