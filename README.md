> ⚠️ **Proprietary — All Rights Reserved.** Public for portfolio review only. No part may be copied, used, modified, or redistributed without written permission.

# SaaS Platform

Multi-tenant B2B Logistics & Warehouse Management SaaS — early build, actively developed.

A working foundation for running warehouses, inventory, orders, deliveries, and drivers from one system, with smart dispatch, live tracking, and analytics.

## Status

Under construction.

Core loop is implemented and tested end to end (order → reserve → pick/pack → dispatch → route → track → analytics). Many production-grade features are still planned: returns, delivery time windows, real notification providers, batch tracking, deeper analytics, integrations, mobile apps, and deployment.

Roughly:
- ~65% done from a portfolio-demo perspective
- ~35% done from a production-logistics perspective

See docs/03-roadmap.md for the full picture.

## What works today

- Multi-tenant organizations with strict data isolation
- Auth: JWT access + rotating refresh, bcrypt, invitations, password reset
- RBAC across 6 roles (super admin, org admin, warehouse manager/staff, dispatcher, driver)
- Warehouses, zones, locations
- Products, stock, movements, reservations, low-stock alerts, transfers
- Customers, orders, order items, full lifecycle with history
- Deliveries, packages, status, POD fields, public tracking token
- Drivers, vehicles, shifts, positions
- Smart driver assignment (distance + workload + vehicle capacity)
- Route builder with nearest-neighbor ordering, ETAs, and recalculation
- Real-time: WebSocket + Redis pub/sub + transactional outbox
- Notifications: templates, providers (console stubs), auto-trigger from events
- Analytics: daily rollups, ranges, avg delivery time, top products, CSV export
- Super-admin console: tenant stats, org list, activate/suspend

## What's missing

Planned but not yet built — see docs/03-roadmap.md:

- Returns / RMA
- Delivery time windows and attempts
- Barcode scanning / mobile WMS
- Batch / lot / serial tracking
- Purchase orders and supplier management
- Real email / SMS / push providers
- Customer portal
- Multi-warehouse order splitting
- Deeper analytics (OTIF, cost/km, utilization)
- Real routing with live traffic
- Integrations (Shopify, Stripe, QuickBooks, Mapbox, Twilio)
- E2E tests (Playwright)
- Production deployment (AWS)

## Architecture

Backend
- Python 3.11 · FastAPI · Pydantic v2
- SQLAlchemy 2.0 · Alembic
- PostgreSQL 16
- Redis · Celery (queues, retries, DLQ, beat)
- WebSockets (Redis pub/sub fanout)
- JWT auth · RBAC · tenant isolation · audit log
- Idempotency middleware · rate limiting · request IDs
- Prometheus metrics · structured JSON logs

Frontend
- React · TypeScript · Vite · TailwindCSS v4
- Apple-inspired dark theme, purple accent, pastel statuses
- Role-specific layouts: admin / dispatcher / driver / warehouse
- React Query · Zustand · Leaflet · Recharts
- Skeleton loaders · toasts · top progress bar

Infrastructure
- Docker Compose (db, redis, api, worker, beat, outbox, prometheus, grafana, frontend)
- GitHub Actions CI: lint → audit → migrations → tests (139 passing) → frontend build

## Engineering highlights

- Modular — one bounded context per module
- Transactional outbox — reliable domain events, at-least-once
- Unit of Work — one transaction per request, injected
- Multi-tenant by default — organization_id on every row
- Tested — unit + integration through real HTTP + real Postgres
- Documented — architecture, ERD, ADRs, threat model, runbook, and more

## Docs

- docs/01-architecture.md — system design
- docs/02-erd.md — database model
- docs/03-roadmap.md — phased plan
- docs/04-backend.md — module reference
- docs/05-frontend.md — React guide
- docs/06-ui-ux.md — design system
- docs/07-api.md — REST catalog
- docs/08-testing.md — test strategy
- docs/09-observability.md — logs, metrics, tracing
- docs/10-runbook.md — on-call playbook
- docs/11-deployment.md — local + AWS
- docs/12-onboarding.md — day-1 guide
- docs/13-glossary.md — terms
- docs/14-changelog.md — releases
- docs/15-contributing.md — how to contribute
- docs/adr/ — architecture decisions

## Quick start

cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Grafana: http://localhost:3000

Super admin (if SUPER_ADMIN_EMAIL + SUPER_ADMIN_PASSWORD are set in .env):
- Org: platform

## Tests

docker compose exec api pytest -q

139 tests · 86% coverage · CI runs on every push.

## Roadmap

See docs/03-roadmap.md.

## License

Proprietary. Public for portfolio review only. No part may be copied, used, modified, or redistributed without written permission.