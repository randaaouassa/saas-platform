# Glossary

Terms used across the codebase and docs.

## Platform & tenancy

- **Tenant / Organization** — an isolated customer workspace. Every tenant-owned row carries `organization_id`.
- **Multi-tenancy** — shared database and schema, isolation enforced by `organization_id` on every table and every query.
- **Org slug** — a short unique identifier (`acme`). Required at login because the same email may exist in multiple orgs.
- **Super Admin** — platform operator. Only role that can cross tenants. Lives in the `platform` organization.
- **Org Admin** — tenant owner. Manages users, roles, warehouses, and all tenant data.

## Roles

- **RBAC** — Role-Based Access Control. Roles are granted per user. Enforced by `require_roles(...)` on routes and in services.
- **Permission (concept)** — future: fine-grained `<resource>:<action>` strings. Not enforced yet.
- **Primary role** — the highest-priority role a user has, used by the frontend for routing. Order: `org_admin` > `warehouse_manager` > `warehouse_staff` > `dispatcher` > `driver`.

## Auth

- **Access token** — short-lived JWT (15 min). Sent as `Authorization: Bearer …`.
- **Refresh token** — long-lived (7 days), single-use, rotated on every refresh. Stored hashed in `sessions`.
- **jti** — JWT ID claim, unique per token. Enables future revocation.
- **Session** — DB record of an issued refresh token. Revoked on logout or reuse detection.
- **Invitation** — one-time link to join a workspace with a role. Raw token returned once; only the SHA-256 hash is stored.

## Warehouse & inventory

- **Warehouse** — physical location (address, timezone).
- **Zone** — subdivision inside a warehouse (receiving, storage, packing…).
- **Location** — a specific bin/shelf inside a zone.
- **SKU** — Stock Keeping Unit. Unique per organization.
- **Stock** — quantity of a product at a (warehouse, location). Split into `quantity` and `reserved_quantity`.
- **Available** — `quantity - reserved_quantity`.
- **Movement** — immutable log entry of a stock change: receipt, adjustment, transfer_in/out, reservation, release, ship.
- **Reservation** — temporary hold on stock for an order. Released (undo) or consumed (ship).
- **Transfer** — moving stock between warehouses. Writes `transfer_out` + `transfer_in` movements.
- **Low-stock alert** — threshold per (product, warehouse). Triggers when available ≤ threshold.

## Orders

- **Order** — customer request for one or more products from a warehouse.
- **Order item** — product + quantity + unit price + line total.
- **Order lifecycle** — draft → confirmed → reserved → picking → packed → ready_for_dispatch → dispatched → delivered (or cancelled / on_hold).
- **Status history** — audit trail of every transition with actor and reason.
- **CSV import** — bulk order creation. Creates missing customers.

## Delivery

- **Delivery** — a job to move packages from a pickup to a dropoff.
- **Package** — a parcel with code, weight, dimensions. Belongs to one delivery.
- **POD (Proof of Delivery)** — photo, signature, OTP, or note captured at dropoff.
- **Public token** — a random string on each delivery used for the customer-facing tracking page (no auth).
- **Failed delivery** — status transition requiring a `failed_reason`.
- **Reschedule** — moves a failed/pending delivery to a new scheduled time.

## Drivers

- **Driver** — ops record. May or may not be linked to a User (login).
- **Vehicle** — plate, type, capacity weight and volume. Can be assigned to a driver.
- **Shift** — a working window. Start sets driver status to `available`; end sets `offline`.
- **Position** — a recorded GPS snapshot (lat, lng, heading, speed). Time-series.
- **Driver status** — `offline | available | assigned | on_delivery | on_break`.

## Dispatch

- **Candidate** — a driver considered for a delivery.
- **Score** — weighted ranking: 0.7 × distance-to-pickup + 0.3 × workload. Halved if vehicle capacity is insufficient.
- **Assignment** — link between a delivery and a driver (+ optional vehicle). Statuses: `offered | accepted | rejected | expired | completed`.
- **Auto-assign** — assigns the top-scored candidate.
- **Reassign** — replaces the active assignment with a new driver; the old one becomes `rejected`.
- **Unassign** — expires active assignments; the delivery returns to pending.

## Routing

- **Route** — an ordered list of stops for one driver on one date.
- **Stop** — a delivery in a route with `sequence`, `eta`, and status.
- **Nearest-neighbor** — greedy ordering algorithm used to build/rebuild routes.
- **Recalculation** — reorders pending stops. Each call logged in `route_recalculations` with before/after.

## Real-time

- **WS** — WebSocket. Endpoint `/ws/tracking` with JWT in query string.
- **Topic** — one of `delivery`, `driver`, `dispatcher`, `notification`. Subscribed per connection.
- **Pub/sub** — Redis channel fanout. Each event is published to `ws:org:<id>:<topic>`.
- **Live dot** — the green/red indicator in the layout showing WS connectivity.

## Events

- **Domain event** — a fact that happened in the system (`order.confirmed`, `delivery.assigned`…).
- **Outbox** — `domain_events` table written in the same transaction as the state change. Guarantees at-least-once delivery.
- **Dispatcher** — the worker loop that reads unpublished events, publishes to Redis/WS, and runs the notification consumer.
- **Envelope** — the JSON shape of a published event: `event_id`, `type`, `occurred_at`, `org_id`, `actor_id`, `aggregate_*`, `version`, `payload`.

## Notifications

- **Channel** — `inapp | email | sms | push`.
- **Template** — a small registry mapping an event type to subject + body. `{}` placeholders rendered from the event payload.
- **Notification delivery** — per-channel row tracking provider, attempts, status.

## Analytics

- **Fact table** — daily aggregate (`fact_orders_daily`, `fact_deliveries_daily`, `fact_driver_daily`, `fact_inventory_daily`).
- **Rebuild** — idempotent recomputation of a day's facts.
- **Range** — time-series query across a date range with totals, avg delivery time, and top products.

## Ops

- **DLQ** — Dead Letter Queue. Tasks that fail after max retries land in the `dlq` queue.
- **Beat** — Celery scheduler for periodic tasks.
- **Rate limit** — Redis token bucket per route (login 10/5m, register 5/h, …).
- **Idempotency** — `Idempotency-Key` header cached response for 24h. Prevents duplicate work on retries.
- **Request ID** — `X-Request-Id` header. Auto-generated if missing. Propagated to logs and error responses.
- **Problem+JSON** — RFC 7807 error format used across the API.
- **RED metrics** — Rate, Errors, Duration. Standard HTTP service metrics.
- **SLO** — Service Level Objective. See architecture doc.

## Common abbreviations

- **POD** — Proof of Delivery
- **SKU** — Stock Keeping Unit
- **UoW** — Unit of Work
- **RBAC** — Role-Based Access Control
- **JWT** — JSON Web Token
- **WS** — WebSocket
- **DLQ** — Dead Letter Queue
- **ERD** — Entity Relationship Diagram
- **ADR** — Architecture Decision Record
- **SLO** — Service Level Objective
- **RPO** — Recovery Point Objective
- **RTO** — Recovery Time Objective