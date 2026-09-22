# Testing Strategy

Confidence-first, layered, cheap to run. CI gates every push.

## Goals

- Fast feedback: full suite in < 60s in Docker
- Real HTTP through FastAPI (integration over mocks)
- Real Postgres in a dedicated test DB
- No shared state between tests
- Catch regressions in: auth, RBAC, tenant isolation, lifecycle rules,
  invariants (stock, reservations), scoring, pagination, rate limits

## Layers

1. **Unit** — pure functions, no I/O
   - security: hashing, JWT roundtrip, invalid tokens
   - pagination: cursor encode/decode, params validation
   - filters: sort parsing
   - scoring: distance/workload/capacity math
   - haversine: known distances, symmetry
   - rate limit: rule matching
   - celery config: queues, routes, timeouts, beat schedule

2. **Integration** — FastAPI `TestClient` against real Postgres
   - auth: register, login, refresh rotation, logout, me, RBAC
   - users: list, invite, accept, deactivate, role assign/revoke, forgot/reset
   - warehouse: CRUD, zones, locations, tasks, delete cascade
   - inventory: products, receive, adjust, transfer, reservations, alerts, movements
   - orders: create, items, transitions, reservations lifecycle, cancel, import
   - deliveries: lifecycle, reschedule, POD, public token
   - drivers: profile, vehicles, shifts, positions
   - dispatch: ranking, capacity affect, assign, reassign, unassign
   - routing: create, ordering, add/remove stop, status, recalc
   - tracking: WS handshake, events, public tracking
   - notifications: channels, mark read, tenant isolation
   - analytics: rebuild, range, avg time, exports
   - system: version, stats, super admin gating, org suspend
   - events: emit, dispatcher publish, auto notifications

3. **Frontend** — build check + manual
   - `npm run build` must pass in CI
   - E2E (Playwright) planned

## Layout

backend/tests/
  conftest.py
  unit/
    test_security.py
    test_pagination.py
    test_filters.py
    test_scoring.py
    test_haversine.py
    test_rate_limit.py
    test_celery_config.py
    test_idempotency.py
  integration/
    test_auth.py
    test_users.py
    test_warehouse.py
    test_inventory.py
    test_orders.py
    test_deliveries.py
    test_drivers.py
    test_dispatch.py
    test_routing.py
    test_tracking.py
    test_notifications.py
    test_analytics.py
    test_system.py
    test_events.py

## Fixtures (conftest.py)

- Session fixture: creates `saas_platform_test` DB if missing
- Engine fixture: `Base.metadata.create_all`
- `_patch_sessionlocal` (autouse): points `SessionLocal` in core.db,
  core.uow, events.dispatcher at the test engine
- `db`: fresh session per test, truncates all tables before yield
- `client`: TestClient with `get_uow` dependency overridden to the test session
- `org_payload`: unique slug + email generator

Isolation: every test gets a clean DB. Unique slugs/SKUs/codes prevent collisions
even if cleanup misbehaves.

## Conventions

- `_register(client)` returns a token for a fresh tenant
- `_h(tok)` returns the auth header dict
- Every test creates its own data — no shared fixtures beyond client + DB
- No mocks for DB. Only mock external providers (email/SMS).
- Assert on status codes and response body shape.
- For lifecycle tests, walk the entire path in one test.

## Running

Locally:
  docker compose exec api pytest -q

Single file:
  docker compose exec api pytest tests/integration/test_orders.py -v

With coverage:
  docker compose exec api pytest --cov=app --cov-report=term-missing

## CI

`.github/workflows/ci.yml`
- Backend job
  - Postgres + Redis service containers
  - `pip install -e ".[dev]"`
  - `ruff check app tests`
  - `pip-audit` (non-blocking)
  - `alembic upgrade head`
  - `pytest --cov=app --cov-fail-under=70`
- Frontend job
  - Node 20
  - `npm ci`
  - `npm run build`

## Coverage

Current: 86% overall, 139 tests.
Gate: 70%. Raise gradually as modules stabilize.

Known low-coverage spots (accepted for now):
- celery task bodies (run in workers, not in HTTP tests)
- providers (external I/O stubs)
- worker/outbox loop

## Rules for adding tests

- New endpoint → at least one integration test
- New service function → at least one integration test through HTTP
- New pure function → unit test
- New invariant (stock, reservations, state machine) → test the failure case
- RBAC → test both allowed and forbidden
- Tenant isolation → test cross-org access returns 404 or empty

## Anti-patterns

- Sleeping in tests
- Sharing mutable state across tests
- Asserting on exact timestamps
- Asserting on UUID values (except equality)
- Skipping cleanup between tests
- Hitting real external services