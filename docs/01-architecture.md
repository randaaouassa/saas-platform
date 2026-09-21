# Architecture

Version: 1.0
Status: Living document

## 1. Purpose
Architecture of a multi-tenant B2B Logistics & Warehouse Management SaaS.
Covers domains, data, runtime, security, reliability, observability, scale.

## 2. System Context
Actors: Super Admin, Org Admin, Warehouse Manager, Warehouse Staff, Dispatcher, Driver, End Customer.
External: Email (SES), SMS, Maps/Routing provider, S3, Payments (future).
Flows: order ingestion → reserve → pick → pack → dispatch → assign driver → route → track → POD → analytics.

## 3. Principles
1. Domain-first. 2. Tenant-safe by default. 3. Idempotent commands.
4. Async for slow/external work. 5. Fail loudly, degrade gracefully.
6. Observable end-to-end. 7. Backward compatible. 8. IaC only.

## 4. Bounded Contexts
| Context | Owns |
|---|---|
| Identity | users, sessions, invitations |
| Tenancy | organizations |
| Access Control | roles, permissions, role_permissions, user_roles |
| Warehouse | warehouses, zones, locations, tasks |
| Inventory | products, stock, stock_movements, reservations |
| Orders | customers, orders, order_items |
| Delivery | deliveries, packages, pod |
| Drivers | drivers, vehicles |
| Dispatch | assignments, dispatch_events |
| Routing | routes, route_stops |
| Tracking | driver_positions, tracking_events |
| Notifications | notifications, notification_deliveries |
| Analytics | fact tables, MVs |
| Audit | audit_log |

Sync: module interfaces. Async: domain events (Redis Streams → Kafka later).

## 5. State Machines
Order: draft → confirmed → reserved → picking → packed → ready_for_dispatch → dispatched → delivered. Also cancelled, on_hold.
Delivery: pending → assigned → picked_up → in_transit → delivered. Also failed → rescheduled|returned, cancelled (pre-pickup).
Driver: offline ↔ available ↔ assigned ↔ on_delivery → available (on_break).
Stock movement types: receipt, transfer_out, transfer_in, adjustment_+, adjustment-, reservation, release, pick, pack, ship, return.

## 6. Data Model
- Tenancy: shared DB/schema; every tenant table has organization_id; composite indexes lead with org_id; optional Postgres RLS as defense-in-depth.
- IDs: UUIDv7 app-side.
- Timestamps: timestamptz UTC; created_at/updated_at; soft delete via deleted_at.
- Money: numeric(14,2) + currency.
- Quantities: numeric(14,3).
- Geo: lat/lng doubles + PostGIS geography(Point) for hot spatial queries.
- Events: transactional outbox `domain_events`; dispatcher → Redis Streams; at-least-once; consumers idempotent on event_id.
- Partitioning: monthly for stock_movements, tracking_events, audit_log, domain_events.
- Retention: tracking 90d hot + S3; audit 2y; POD 7y; PII delete ≤30d on request.

## 7. API Conventions
- Base `/api/v1`; additive; breaking → `/api/v2`.
- Bearer JWT. Tenancy from token only.
- `Idempotency-Key` required on state-changing POST/PUT.
- Cursor pagination, default 25 max 100. Filter `filter[field][op]=`, sort `?sort=-created_at`.
- Errors: RFC 7807 + trace_id. `X-Request-Id` echoed.
- Rate limits documented per group.

## 8. Runtime
Services: api, worker-default, worker-routing, worker-notifications, scheduler, outbox-dispatcher, ws-gateway, postgres (RDS Multi-AZ), redis (ElastiCache), s3.
Networking: ALB → api (private subnets); workers no inbound; data stores private.
Envs: local, dev, staging, prod. Config via env + Secrets Manager.

## 9. Reliability
SLOs: API 99.9%; read p95 ≤250ms; write p95 ≤400ms; assignment p95 ≤2s; route p95 ≤5s (10 stops); tracking lag p95 ≤3s; order→delivery ≤60s.
Failures: DB primary down → Multi-AZ failover <60s; Redis down → DB reads + queue pause + WS reconnect; routing provider down → cached route or straight-line fallback; worker backlog → autoscale + DLQ; outbox down → alert + replay; WS down → reconnect/backoff + REST fallback; email down → retry + fallback provider.
DR: RPO 5m, RTO 60m; cross-region backups; quarterly runbooks.
Backpressure: 429 + Retry-After; bounded queues; WS rate limit; drop slow consumers.

## 10. Security
AuthN: bcrypt(12); access 15m; refresh 7d rotating single-use; reuse → revoke family; MFA optional.
AuthZ: permissions `<resource>:<action>`; role→perms in DB; enforcement route+service; deny by default.
Rate limits: login 10/5m/IP; register 5/h/IP; auth'd 600/min; WS 30/min/conn; public tracking 60/min/IP.
Data: TLS, encryption at rest, Secrets Manager rotation ≤90d, PII masked in logs, audit privileged actions.
AppSec: Pydantic validation, ORM only, SSRF allowlist, safe uploads, strict CORS, security headers, dependency scanning in CI.

## 11. Observability
Logs: structured JSON (ts, level, service, env, request_id, trace_id, org_id, user_id, msg); no PII.
Metrics: RED per endpoint, USE per infra, business (orders/min, assignment time, route time, tracking lag), queue/DLQ/outbox.
Tracing: OpenTelemetry, W3C context.
Health: /health/live, /health/ready, /metrics.
Alerts: error rate >1%/5m; p95 > SLO 10m; DLQ > 0; outbox lag >30s; DB conn >80%.

## 12. Events
Envelope: event_id, type, occurred_at, org_id, actor, version, payload.
Core: org.created, user.invited/joined, warehouse.created, stock.received/moved/adjusted, order.created/confirmed/reserved/packed/cancelled, delivery.created/assigned/picked_up/delivered/failed, driver.status_changed/location_updated, route.optimized/recalculated, notification.queued/sent/failed.
Semantics: at-least-once; dedupe on event_id; per-aggregate ordering via stream key.

## 13. Scale Targets
Orgs 1k→100k; users/org 100→10k; orders/day/org 10k→1M; deliveries/day 1M→20M; concurrent drivers 10k→500k; tracking events/s 5k→100k; API RPS 2k→50k.

## 14. Cost & Ops
Autoscale workers on queue depth; RDS sized from p95 + headroom; S3 lifecycle to Glacier after 90d; logs 30d hot / 1y cold.

## 15. Change Management
Additive migrations within release; expand→migrate→contract; feature flags; API deprecation 6 months + Sunset header.

## 16. Glossary
Tenant, SKU, POD, DLQ, Outbox, RLS.