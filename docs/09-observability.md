# Observability

Three pillars: logs, metrics, traces. Plus health checks and alerts.

## Logs

Structured JSON via structlog. Written to stdout.

Every log carries context:
- timestamp (ISO UTC)
- level
- service (e.g. "app", "events.dispatcher", "worker.outbox")
- env
- request_id (from RequestIDMiddleware, propagated via structlog contextvars)
- trace_id (when OpenTelemetry is enabled)
- event (short key)
- structured fields

Example:
{
  "event": "startup",
  "level": "info",
  "env": "local",
  "app": "saas-platform",
  "timestamp": "2026-01-01T00:00:00Z"
}

{
  "event": "app_error",
  "level": "warning",
  "code": "not_found",
  "message": "order not found",
  "path": "/api/v1/orders/123",
  "request_id": "9c9f18bb…"
}

Rules:
- Never log secrets, tokens, passwords, or full PII.
- Log the domain event, not the payload, when payloads may contain PII.
- Always include request_id when in a request scope.

## Request IDs

`RequestIDMiddleware`:
- Reads `X-Request-Id` from the client or generates a hex UUID
- Binds to structlog contextvars
- Stores on `request.state.request_id`
- Echoes back in `X-Request-Id`

Error responses include `trace_id` from `request.state.request_id`.

## Metrics

Prometheus exposition at `/metrics` (unauthenticated, excluded from rate limit).

**HTTP metrics (RED)**
- `http_requests_total{method, path, status}` — counter
- `http_request_duration_seconds{method, path}` — histogram

Path labels use the FastAPI route pattern (e.g. `/api/v1/orders/{order_id}`),
never raw URLs, to keep cardinality low.

**Business metrics**
- `domain_events_unpublished_total` — gauge, updated by the outbox worker

**Python defaults**
- GC stats, process memory, Python version — automatic from `prometheus_client`

## Health

- `GET /health/live` — process up (no dependencies)
- `GET /health/ready` — process ready (currently trivially true; extend with DB/Redis checks in prod)

Both are excluded from rate limiting. Both return 200.

## Tracing

`app/core/otel.py` sets up a `TracerProvider` with the service name + env.
Local dev: `ConsoleSpanExporter`.
Prod: switch to OTLP exporter (collector endpoint).

Spans expected for: HTTP requests, DB queries, Redis calls, Celery tasks,
external HTTP (routing provider).

## Dashboards

Grafana provisioned via `infra/observability/grafana/`.

Provisioned dashboards:
- **Overview** — RPS, error rate, p95 latency, unpublished domain events
- **API** — requests by path + method, p50/p95/p99 latency

Datasource: Prometheus at `http://prometheus:9090`.

Access: http://localhost:3000 (admin/admin in dev).

## Alerts

Provisioned in `infra/observability/prometheus/alerts.yml`.

- **ApiDown** — `up{job="api"} == 0` for 1m (critical)
- **HighErrorRate** — 5xx rate / total > 1% for 5m (critical)
- **HighLatencyP95** — p95 > 400ms for 10m (warning)

Extended (recommended, not yet wired):
- DLQ size > 0
- Outbox lag > 30s
- DB connection pool exhaustion
- Redis unavailable

## Outbox monitoring

The outbox worker (`app/worker/outbox.py`) publishes domain events and updates
the `domain_events_unpublished_total` gauge each cycle. If the gauge stays
above zero, alerts should fire.

Query:
`domain_events_unpublished_total`

## Celery

- Task failures logged by `celery_dlq.on_task_failure`
- After `max_retries`, task is sent to the `dlq` queue
- DLQ monitored by queue depth metric (add when moving to prod)

Recommended Celery metrics:
- `celery_queue_length{queue=...}`
- `celery_task_failed_total{task=...}`
- `celery_task_succeeded_total{task=...}`

## Frontend

- `TopProgressBar` shows any active fetch or mutation
- WS connection state shown in every layout (Live/Offline dot)
- Toasts surface all non-auth API errors
- React Query devtools (dev only)

## Recommended prod additions

- Sentry for exception tracking (backend + frontend)
- OpenTelemetry collector + Tempo/Jaeger for traces
- CloudWatch or Loki for log aggregation
- Alertmanager routes to Slack/PagerDuty
- Uptime checks on `/health/live` from an external prober

## Anti-patterns

- Logging request bodies
- High-cardinality metric labels (user_id, order_id)
- Metrics for things nobody will alert on
- Health checks that hit slow dependencies
- Alerts without an action (everything must have a runbook entry — see 10-runbook.md)