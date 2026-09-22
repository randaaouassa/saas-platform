> ⚠️ **Proprietary — All Rights Reserved.** Public for portfolio review only. No part may be copied, used, modified, or redistributed without written permission.

# SaaS Platform

Multi-tenant B2B Logistics & Warehouse Management SaaS.

A single platform for organizations to manage warehouses, inventory, customer orders, delivery operations, and drivers — with real-time tracking, smart driver assignment, route optimization, and operational analytics.

## Vision

Give logistics businesses one system to run their entire operation: Customer order → inventory check → pick & pack → delivery creation → driver assignment → route optimization → live tracking → proof of delivery → analytics.

## Core Modules

| # | Module | Purpose |
|---|--------|---------|
| 1 | Auth & Organizations | Multi-tenant auth, JWT, RBAC, invitations |
| 2 | Warehouse Management | Warehouses, zones, receiving, picking, packing, transfers |
| 3 | Inventory | SKUs, stock, movements, reservations, alerts, history |
| 4 | Order Management | Orders, items, lifecycle, reservation, cancellation |
| 5 | Delivery Management | Jobs, packages, status, POD, failed handling |
| 6 | Driver Management | Profiles, vehicles, shifts, positions, workload |
| 7 | Smart Driver Assignment | Ranked driver matching by distance, capacity, load |
| 8 | Route Optimization | Multi-stop sequencing, ETA, recalculation |
| 9 | Real-Time Tracking | Live location, status, dispatcher & driver dashboards |
| 10 | Notifications | In-app, email, delivery, assignment, low-stock |
| 11 | Analytics | Orders, inventory, deliveries, drivers, costs |
| 12 | System | Super-admin: tenant stats, org management |
| 13 | Domain Events | Transactional outbox, dispatcher, auto WS publish |

## User Roles

- **Super Admin** — platform operator
- **Organization Admin** — tenant owner
- **Warehouse Manager / Staff** — warehouse operations
- **Dispatcher** — delivery queue + assignment
- **Driver** — mobile-friendly delivery console

## Architecture

**Backend**
- Python 3.11 · FastAPI · REST · Pydantic v2
- SQLAlchemy 2.0 · Alembic migrations
- Celery + Redis (async jobs, retries, DLQ, beat schedules)
- WebSockets for live updates (Redis pub/sub fanout)
- JWT auth (access + rotating refresh) · RBAC · tenant isolation · audit logging
- Idempotency middleware · rate limiting · request ID propagation
- Prometheus metrics · OpenTelemetry hooks · structured JSON logs

**Database**
- PostgreSQL 16
- Relational schema, indexes, transactions
- Organization-level row isolation (organization_id on every table)
- Transactional outbox (domain_events) for reliable event publishing
- Daily fact tables for analytics

**Frontend**
- React · TypeScript · Vite · TailwindCSS v4
- Apple-inspired dark theme, purple accent, pastel statuses
- Role-specific layouts (admin / dispatcher / driver / warehouse)
- React Query · WebSocket client · Zustand
- Recharts (analytics) · Leaflet (maps) · skeleton loaders

**Infrastructure**
- Docker · Docker Compose (db, redis, api, worker, beat, outbox, prometheus, grafana, frontend)
- AWS target (ECS · RDS · ElastiCache · S3 · CloudWatch)
- GitHub Actions CI (lint → audit → migrate → tests → build)

## Engineering Principles

- **Modular** — each domain is a self-contained module
- **Scalable** — stateless services, horizontal scaling, async workloads
- **Secure** — least privilege, validated input, rate limiting, audit trail
- **Observable** — structured logs, metrics, tracing, health checks
- **Tested** — unit, integration, API, auth tests in CI (139 passing)
- **Extensible** — new tenants, warehouses, drivers, orders need no redesign

## Repository Layout

- backend/ — FastAPI app, modules, migrations, tests
- frontend/ — React app
- infra/ — Observability configs, deployment
- docs/ — Architecture, ERD, roadmap, ADRs, threat model

## Quick Start

- cp .env.example .env
- docker compose up -d --build
- docker compose exec api alembic upgrade head

Endpoints:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Grafana: http://localhost:3000

Super admin (if SUPER_ADMIN_EMAIL + SUPER_ADMIN_PASSWORD set in .env):
- Org: platform
- Login with the configured email/password

## Tests

docker compose exec api pytest -q

139 passing · 86% coverage · CI runs on every push.

## Roadmap

See docs/03-roadmap.md.

## Status

Backend complete. Frontend core complete. Deployment + polish in progress.