# Backend Reference

FastAPI service powering the SaaS Platform. Modular monolith organized by bounded context.

## Stack

- Python 3.11
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async-ready, sync in use)
- Alembic migrations
- PostgreSQL 16
- Redis (cache, rate limits, pub/sub, Celery broker)
- Celery (background jobs + beat)
- structlog (structured logs)
- Prometheus client (metrics)

## Layout

backend/
  app/
    core/        config, db, uow, security, logging, errors,
                 metrics, middleware, idempotency, rate_limit,
                 otel, celery_app, celery_beat, celery_dlq,
                 cleanup_tasks, bootstrap, ids, audit
    shared/      mixins, pagination, filters, repository
    modules/
      identity/  orgs, users, roles, invitations, sessions, password reset
      warehouse/ warehouses, zones, locations, tasks
      inventory/ products, stock, movements, reservations, alerts
      orders/    customers, orders, items, lifecycle
      deliveries/ deliveries, packages, status, POD
      drivers/   drivers, vehicles, shifts, positions
      dispatch/  candidates, assignments, scoring
      routing/   routes, stops, recalculation
      tracking/  WS + tracking events + public tracking
      notifications/ notifications, deliveries, templates, providers
      analytics/ daily facts, ranges, exports
      system/    version, tenant stats (super admin)
    worker/
      outbox.py  dispatch loop for domain events
    main.py
  alembic/
  tests/

## Core concepts

### Config
`app/core/config.py` — pydantic-settings. Reads `.env`. Fails fast in prod if SECRET_KEY missing or DEBUG true.

### Unit of Work
`app/core/uow.py`. Wraps a SQLAlchemy session. Services accept `uow: UnitOfWork` and never open sessions themselves. Commit once per request.

### Errors
`app/core/errors.py`. All application errors inherit `AppError`. Handlers return RFC 7807 problem+json with `trace_id`.

### Security
`app/core/security.py`.
- bcrypt password hashing (max 72 bytes, truncated)
- JWT access (15 min) + refresh (7 days, rotating, stored hashed)
- `jti` on every token to allow uniqueness + future revocation

### Rate limiting
`app/core/rate_limit.py`. Redis token-bucket. Per-route rules. Disabled in tests via `RATE_LIMIT_ENABLED=false`.

### Idempotency
`app/core/idempotency.py`. `Idempotency-Key` header on state-changing requests. Cached response for 24h.

### Audit
`app/core/audit.py`. Every mutating service writes an audit row (actor, resource, action, metadata).

### Events (outbox)
`app/core/events/`. `emit()` inside a service writes to `domain_events` in the same transaction. `app/worker/outbox.py` dispatches: publishes to Redis (WS) and runs consumer (auto notifications).

### Metrics
`app/core/metrics.py`. RED metrics via `MetricsMiddleware`. `/metrics` exposed.

### Celery
`app/core/celery_app.py` — queues: default, notifications, routing, analytics, dlq.
`celery_beat.py` — schedules (analytics rollup, cleanups, dispatch sweep).
`celery_dlq.py` — moves failed tasks after max retries.

## Modules

Each module follows:
- models.py — SQLAlchemy models
- schemas.py — Pydantic DTOs
- service.py — business logic (accepts `uow`)
- deps.py — module-specific dependencies (only identity)
- router.py — FastAPI endpoints

### identity
- Multi-tenant orgs, users, roles (RBAC)
- Register creates org + default roles + admin
- Login by `(org_slug, email)` because an email can belong to multiple orgs
- Invitations: raw token returned once, only hash stored
- Password reset via one-time token (1h TTL)
- Accept invite auto-creates driver profile if role is driver

Endpoints under `/auth`, `/users`, `/roles`.

### warehouse
Warehouses → zones → locations. Tasks (receiving/pick/pack/transfer/adjust). Lifecycle: pending → in_progress → completed | cancelled.

### inventory
Products (SKU), stock per (product, warehouse, location), movements, reservations, alerts.
- Receipts + adjustments write movements
- Reservations decrement available; release or consume
- Low-stock alerts trigger when on_hand ≤ threshold
- Transfers move quantity between warehouses with two movements

### orders
Customers → orders → items → status history.
Lifecycle: draft → confirmed → reserved → picking → packed → ready_for_dispatch → dispatched → delivered.
- On `reserved`, stock is reserved across all items
- On `cancelled`, active reservations released
- On `dispatched`, reservations consumed
- CSV import creates customers if needed

### deliveries
Delivery jobs + packages + POD.
Lifecycle: pending → assigned → picked_up → in_transit → delivered | failed → rescheduled | returned.
- `public_token` auto-generated for customer tracking
- Every transition also writes a tracking event (see tracking)

### drivers
Driver profiles (optionally linked to a user), vehicles, shifts, positions.
- `GET /drivers/me` returns the driver linked to the logged-in user
- Shift start sets status to available; end sets offline
- Position updates are appended (partitioned table in prod)

### dispatch
Smart assignment.
- Candidate ranking combines:
  - distance to pickup (haversine)
  - active deliveries count
  - vehicle capacity vs package weight
- Score = 0.7 × distance + 0.3 × workload, halved if capacity fails
- Auto mode picks top candidate
- Reassign / unassign supported

### routing
- Nearest-neighbor ordering on stop creation
- ETA + total distance/duration computed
- Stop status: pending → arrived → completed | skipped | failed
- Recalculate reorders pending stops; each call logged in `route_recalculations`

### tracking
- WS endpoint `/ws/tracking` with JWT in query, Redis pub/sub fanout
- Tracking events appended on delivery transitions
- Public tracking at `/api/v1/public/track/{token}` — no auth, returns status + history

### notifications
- Channel: inapp / email / sms / push
- Template registry + render
- Providers: console logger stubs (replace with SES/Twilio/FCM)
- Auto-triggered from domain events via outbox consumer

### analytics
- Daily fact tables: orders, deliveries, drivers, inventory
- `/analytics/rebuild?day=` idempotent rollup
- `/analytics/range?from=&to=` returns time series + totals + top products + avg delivery time
- CSV exports for orders and deliveries
- Celery beat rebuilds yesterday for all orgs

### system
- `/system/version`
- `/system/stats` — tenant-wide counters (super_admin only)
- `/system/orgs` + status update (activate/suspend)

## Testing

- Conftest creates a dedicated test DB `saas_platform_test`
- Tables created via `Base.metadata.create_all`
- `SessionLocal` patched to point at test engine (per test)
- Every test tenant uses unique slug/SKU/code to avoid collisions
- 139 tests: unit (security, pagination, scoring, haversine, rate limit config) + integration (full HTTP via TestClient)

Run: `docker compose exec api pytest -q`

## Conventions

- Services never open sessions. Always accept `uow`.
- Routers never touch DB. Always call service.
- All list endpoints: `response_model=list[...]` or `Page[...]`.
- All errors go through `AppError`.
- All state-changing operations write audit + emit domain event.
- File names: snake_case. Classes: PascalCase. Routers: `router`.
- Line length 120 (ruff).

## Extending

Add a module:
1. `app/modules/<name>/` with the 4 files
2. Import models in `app/modules/__init__.py`
3. Add router include in `app/main.py`
4. Add tests in `tests/integration/test_<name>.py`
5. Generate Alembic migration
6. Commit