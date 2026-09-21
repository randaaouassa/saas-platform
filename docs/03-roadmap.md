# Roadmap

Phases are sequential. Each phase ends with a working, tested increment.

## Phase 0 — Foundations
- Repo layout, docs, README
- Docker Compose (Postgres, Redis, API)
- Config, logging, error contracts
- Alembic setup

## Phase 1 — Identity & Tenancy
- Models: organizations, users, roles, permissions, sessions, invitations
- Auth: register, login, refresh, logout, me
- RBAC enforcement + permission matrix
- Invitations flow
- Tests: auth + authz

## Phase 2 — Warehouse
- Warehouses, zones, locations
- Tasks: receiving, pick, pack, transfer, adjust
- APIs + tests

## Phase 3 — Inventory
- Products, stock, reservations, movements, alerts
- Concurrency-safe reservation
- Low-stock alerts
- APIs + tests

## Phase 4 — Orders
- Customers, orders, items, history
- Lifecycle enforcement
- Inventory reservation integration
- APIs + tests

## Phase 5 — Deliveries
- Deliveries, packages, POD, history
- Status lifecycle
- APIs + tests

## Phase 6 — Drivers
- Drivers, vehicles, shifts, positions
- Availability + workload
- APIs + tests

## Phase 7 — Dispatch
- Scoring engine (distance, capacity, load, vehicle)
- Ranked candidates, auto/manual assignment
- APIs + tests

## Phase 8 — Routing
- Multi-stop optimization
- ETA, recalculation triggers
- Async worker
- APIs + tests

## Phase 9 — Real-time
- WebSockets: driver location, delivery status, dispatcher feed
- Redis pub/sub fanout
- Customer tracking page
- Auth + backpressure

## Phase 10 — Notifications
- In-app, email, SMS
- Templates, retries, DLQ
- Triggers from domain events

## Phase 11 — Analytics
- Fact tables + materialized views
- Scheduled rollups
- Dashboards per role

## Phase 12 — Frontend
- Vite + React + TS scaffold
- Auth flow, role-based layouts
- Dashboards: admin, warehouse, dispatcher, driver
- Customer tracking
- WebSocket integration

## Phase 13 — Quality
- Unit, integration, API, auth, frontend tests
- CI: lint → test → build → image
- Coverage gates

## Phase 14 — Production
- Observability (logs, metrics, traces, alerts)
- Secrets, hardening, rate limits
- AWS: ECS, RDS, ElastiCache, S3, ALB
- CD pipeline, migrations as one-off task

## Phase 15 — Scale & Hardening
- Read replicas, caching, partitioning
- Load tests, chaos drills
- DR runbooks