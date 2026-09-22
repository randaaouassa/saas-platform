# API Reference

Base path: `/api/v1`
Auth: `Authorization: Bearer <access_token>`
Errors: RFC 7807 (application/problem+json) with `trace_id`

Live OpenAPI: http://localhost:8000/docs

## Conventions

- IDs are UUIDv7 strings.
- Money is `numeric(14,2)` returned as string; format on the client.
- Quantities are `numeric(14,3)`.
- Timestamps are ISO-8601 UTC with `Z`.
- All list endpoints return an array unless noted.
- Pagination for high-volume endpoints uses cursor (planned rollout).
- Idempotency: send `Idempotency-Key` on POST/PUT that mutates to make retries safe.

## Auth

POST /auth/register
  body: { organization: { name, slug }, email, password, full_name }
  → 201 TokenPair

POST /auth/login
  body: { email, password, organization_slug }
  → 200 TokenPair

POST /auth/refresh
  body: { refresh_token }
  → 200 TokenPair (rotates)

POST /auth/logout
  body: { refresh_token }
  → 204

GET /auth/me
  → 200 { id, email, full_name, roles[], organization_id, is_active, mfa_enabled, created_at }

GET /auth/me/organization
  → 200 { id, name, slug, plan, status, created_at }

POST /auth/invitations            (org_admin)
  body: { email, role_name }
  → 201 { id, email, role_id, expires_at, accepted_at, token }

GET /auth/invitations/validate?token=...
  → 200 { email, role_name, org_name, org_slug, expires_at, accepted_at }

POST /auth/invitations/accept
  body: { token, password, full_name }
  → 201 TokenPair (auto-login; creates user, links role, auto-creates Driver if role is driver)

POST /auth/forgot-password
  body: { email, organization_slug }
  → 200 { sent: true, token } (token only in non-prod)

POST /auth/reset-password
  body: { token, new_password }
  → 200 User

## Users (org_admin)

GET /users
  → list of users with `roles[]`

PATCH /users/{id}
  body: { full_name?, phone?, is_active? }

POST /users/{id}/deactivate

POST /users/{id}/roles
  body: { role_name }

DELETE /users/{id}/roles/{role_name}

## Roles (org_admin)

GET /roles
GET /roles/permissions

## Warehouses

POST /warehouses                    (org_admin, warehouse_manager)
GET /warehouses
GET /warehouses/{id}
PATCH /warehouses/{id}
DELETE /warehouses/{id}

POST /warehouses/{id}/zones
GET /warehouses/{id}/zones
DELETE /warehouses/zones/{zone_id}

POST /warehouses/zones/{zone_id}/locations
GET /warehouses/zones/{zone_id}/locations
DELETE /warehouses/locations/{location_id}

POST /warehouses/tasks
GET /warehouses/tasks/list?warehouse_id=&status_filter=
PATCH /warehouses/tasks/{id}/status
  body: { status }

## Inventory

Products
POST /inventory/products
GET /inventory/products
GET /inventory/products/{id}
PATCH /inventory/products/{id}

Stock
POST /inventory/stock/receive
  body: { product_id, warehouse_id, location_id?, quantity }

POST /inventory/stock/adjust
  body: { product_id, warehouse_id, location_id?, quantity, reason? }

POST /inventory/stock/transfer
  body: { product_id, from_warehouse_id, to_warehouse_id, quantity }

GET /inventory/stock?warehouse_id=

Reservations
POST /inventory/reservations
  body: { product_id, warehouse_id, quantity, ref_type, ref_id, expires_at? }
POST /inventory/reservations/{id}/release?consume=true|false

Movements
GET /inventory/movements?product_id=

Alerts
POST /inventory/alerts
GET /inventory/alerts?only_triggered=
PATCH /inventory/alerts/{id}
POST /inventory/alerts/{id}/resolve
POST /inventory/alerts/low-stock-scan

## Customers

POST /customers
GET /customers
GET /customers/{id}
PATCH /customers/{id}

## Orders

POST /orders
  body: { customer_id, number, currency, notes?, warehouse_id, items[] }

POST /orders/import
  body: { warehouse_id, rows: [ { number, customer_name?, customer_email?, items[] } ] }
  → { created, errors[] }

GET /orders?status_filter=
GET /orders/{id}
PATCH /orders/{id}
POST /orders/{id}/items
DELETE /orders/{id}/items/{item_id}
POST /orders/{id}/cancel
  body: { reason }
POST /orders/{id}/status?warehouse_id=
  body: { status, reason? }
GET /orders/{id}/history

Order lifecycle transitions enforced:
draft → confirmed → reserved → picking → packed → ready_for_dispatch → dispatched → delivered
cancelled allowed from any pre-dispatched state.

## Deliveries

POST /deliveries
  body: { order_id?, customer_id?, pickup_location, pickup_lat?, pickup_lng?,
          dropoff_location, dropoff_lat?, dropoff_lng?, scheduled_at?, packages[] }

GET /deliveries?status_filter=
GET /deliveries/mine                (current user's driver jobs)
GET /deliveries/{id}
PATCH /deliveries/{id}
POST /deliveries/{id}/cancel
  body: { reason }
POST /deliveries/{id}/reschedule
  body: { scheduled_at }
POST /deliveries/{id}/status
  body: { status, lat?, lng?, note?, failed_reason? }
GET /deliveries/{id}/history

POD
POST /deliveries/{id}/pod
  body: { kind, s3_key?, signer_name?, signature_s3_key?, lat?, lng? }
GET /deliveries/{id}/pod

Delivery lifecycle:
pending → assigned → picked_up → in_transit → delivered | failed → rescheduled | returned
cancelled allowed from pending/assigned.

## Drivers

POST /drivers
GET /drivers?status_filter=
GET /drivers/me                     (linked to logged-in user)
GET /drivers/{id}
PATCH /drivers/{id}

Vehicles
POST /drivers/vehicles
GET /drivers/vehicles/list

Shifts
POST /drivers/shifts/start
  body: { driver_id }
POST /drivers/shifts/{id}/end
GET /drivers/shifts/list?driver_id=

Positions
POST /drivers/{id}/positions
  body: { lat, lng, heading?, speed? }
GET /drivers/{id}/positions/latest
GET /drivers/{id}/positions?limit=

## Dispatch (org_admin, dispatcher)

POST /dispatch/candidates
  body: { delivery_id }
  → { delivery_id, candidates[] } where candidate has:
     driver_id, full_name, status, vehicle_id, distance_km,
     active_deliveries, package_weight, vehicle_capacity, capacity_ok,
     score, factors

POST /dispatch/assign
  body: { delivery_id, driver_id?, vehicle_id? }   # driver_id omitted → auto

POST /dispatch/reassign
  body: { delivery_id, new_driver_id, new_vehicle_id?, reason? }

POST /dispatch/unassign
  body: { delivery_id, reason? }

GET /dispatch/assignments?delivery_id=&driver_id=
PATCH /dispatch/assignments/{id}/status
  body: { status }

## Routing (org_admin, dispatcher)

POST /routes
  body: { driver_id, date, delivery_ids[] }
GET /routes?driver_id=
GET /routes/{id}
DELETE /routes/{id}
POST /routes/{id}/start
POST /routes/{id}/complete
POST /routes/{id}/stops
  body: { delivery_id, position? }
DELETE /routes/{id}/stops/{stop_id}
PATCH /routes/stops/{stop_id}/status
  body: { status }
POST /routes/{id}/recalculate
  body: { reason }
GET /routes/{id}/recalculations

## Notifications

POST /notifications                (org_admin, warehouse_manager, dispatcher)
  body: { user_id?, customer_id?, channel, template, payload }
GET /notifications?user_id=&unread_only=
GET /notifications/mine?unread_only=
POST /notifications/mine/read-all
POST /notifications/{id}/read
GET /notifications/{id}/deliveries

## Tracking

WS  /ws/tracking?token=<jwt>&topics=delivery,driver,dispatcher,notification
    Server → client JSON envelopes:
    { event_id, type, occurred_at, org_id, actor_id,
      aggregate_type, aggregate_id, version, payload }

GET /tracking/deliveries/{id}/events

Public (no auth)
GET /public/track/{token}
  → { delivery_id, status, dropoff_location, dropoff_lat, dropoff_lng,
      scheduled_at, delivered_at, history[] }

## Analytics

POST /analytics/rebuild?day=YYYY-MM-DD
GET  /analytics/orders?day=
GET  /analytics/deliveries?day=
GET  /analytics/drivers?day=
GET  /analytics/inventory?day=
GET  /analytics/overview?day=
GET  /analytics/range?from=&to=
GET  /analytics/avg-delivery-time?from=&to=
GET  /analytics/export/orders.csv?from=&to=
GET  /analytics/export/deliveries.csv?from=&to=

## System (super_admin)

GET /system/version
GET /system/stats
GET /system/orgs
PATCH /system/orgs/{id}/status
  body: { status: active | suspended }

## Health / Ops

GET /health/live
GET /health/ready
GET /metrics       Prometheus format
GET /api/v1/ping

## Status codes

200 OK · 201 Created · 204 No Content
400 Bad Request · 401 Unauthorized · 403 Forbidden · 404 Not Found
409 Conflict · 422 Validation Error · 429 Too Many Requests · 500 Internal

## Rate limits

- /auth/login           10 / 5 min / IP
- /auth/register        5 / hour / IP
- /auth/refresh         60 / min
- /auth/invitations     20 / hour
- /api/v1/* (auth'd)    600 / min

Response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
429 responses include Retry-After.

## Errors

{
  "type": "about:blank#validation_error",
  "title": "Invalid input",
  "status": 422,
  "instance": "/api/v1/orders",
  "trace_id": "…",
  "detail": [...]
}