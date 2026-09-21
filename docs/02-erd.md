# ERD & Data Dictionary

Conventions:
- All tenant tables have `organization_id UUID NOT NULL`.
- PKs: UUIDv7.
- Timestamps: `created_at`, `updated_at` timestamptz.
- Soft delete: `deleted_at` where audit matters.
- Money: numeric(14,2) + currency char(3).
- Quantities: numeric(14,3).

## Entities

### Identity & Tenancy
organizations(id, name, slug UNIQUE, plan, status, created_at, updated_at)
users(id, organization_id, email, hashed_password, full_name, phone, is_active, mfa_enabled, last_login_at, created_at, updated_at)
  UNIQUE(organization_id, email)
sessions(id, user_id, refresh_token_hash, expires_at, revoked_at, user_agent, ip, created_at)
invitations(id, organization_id, email, role_id, token_hash, expires_at, accepted_at, invited_by, created_at)

### Access Control
roles(id, organization_id NULL for system roles, name, is_system, created_at)
permissions(id, code UNIQUE, description)
role_permissions(role_id, permission_id) PK(role_id, permission_id)
user_roles(user_id, role_id) PK(user_id, role_id)

### Warehouse
warehouses(id, organization_id, name, code, address, lat, lng, timezone, is_active, created_at, updated_at)
  UNIQUE(organization_id, code)
zones(id, organization_id, warehouse_id, name, code, type, created_at)
  UNIQUE(warehouse_id, code)
locations(id, organization_id, zone_id, code, kind, capacity, created_at)
  UNIQUE(zone_id, code)
warehouse_tasks(id, organization_id, warehouse_id, type, ref_type, ref_id, status, assigned_to, started_at, completed_at, created_at)
  type: receiving|pick|pack|transfer|adjust

### Inventory
products(id, organization_id, sku, name, description, unit, weight, dimensions, barcode, is_active, created_at, updated_at)
  UNIQUE(organization_id, sku)
stock(id, organization_id, product_id, warehouse_id, location_id, quantity, reserved_quantity, updated_at)
  UNIQUE(product_id, warehouse_id, location_id)
stock_movements(id, organization_id, product_id, warehouse_id, location_id, type, quantity, ref_type, ref_id, actor_id, created_at)  [PARTITIONED monthly]
stock_reservations(id, organization_id, product_id, warehouse_id, quantity, ref_type, ref_id, status, expires_at, created_at)
  status: active|released|consumed|expired
stock_alerts(id, organization_id, product_id, warehouse_id, threshold, triggered_at, resolved_at)

### Orders
customers(id, organization_id, name, email, phone, address, lat, lng, external_ref, created_at, updated_at)
orders(id, organization_id, customer_id, number, status, currency, total_amount, notes, placed_at, created_at, updated_at)
  UNIQUE(organization_id, number)
order_items(id, organization_id, order_id, product_id, quantity, unit_price, total_price, created_at)
order_status_history(id, organization_id, order_id, from_status, to_status, actor_id, reason, created_at)

### Delivery
deliveries(id, organization_id, order_id NULL, customer_id, pickup_location, pickup_lat, pickup_lng, dropoff_location, dropoff_lat, dropoff_lng, status, scheduled_at, delivered_at, failed_reason, created_at, updated_at)
packages(id, organization_id, delivery_id, code, weight, length, width, height, volume, created_at)
  UNIQUE(organization_id, code)
delivery_status_history(id, organization_id, delivery_id, from_status, to_status, actor_id, lat, lng, note, created_at)
proof_of_delivery(id, organization_id, delivery_id, kind, s3_key, signer_name, signature_s3_key, lat, lng, captured_at, created_at)
  kind: photo|signature|otp|note

### Drivers
drivers(id, organization_id, user_id NULL, full_name, phone, license_no, status, rating, created_at, updated_at)
  status: offline|available|assigned|on_delivery|on_break
vehicles(id, organization_id, driver_id NULL, plate, type, capacity_weight, capacity_volume, created_at)
  type: bike|van|truck_small|truck_large
driver_shifts(id, organization_id, driver_id, started_at, ended_at, status)

### Dispatch
assignments(id, organization_id, delivery_id, driver_id, vehicle_id, score, mode, status, assigned_by, assigned_at, completed_at, created_at)
  mode: auto|manual
  status: offered|accepted|rejected|expired|completed
dispatch_events(id, organization_id, delivery_id, candidate_driver_id, score, factors_json, created_at)

### Routing
routes(id, organization_id, driver_id, date, status, total_distance_m, total_duration_s, created_at, updated_at)
  status: planned|active|completed|cancelled
route_stops(id, organization_id, route_id, delivery_id, sequence, eta, arrived_at, departed_at, status)
  UNIQUE(route_id, sequence)
route_recalculations(id, organization_id, route_id, reason, before_json, after_json, created_at)

### Tracking
driver_positions(id, organization_id, driver_id, lat, lng, heading, speed, recorded_at)  [PARTITIONED monthly]
tracking_events(id, organization_id, delivery_id, type, lat, lng, payload_json, created_at)  [PARTITIONED monthly]

### Notifications
notifications(id, organization_id, user_id NULL, customer_id NULL, channel, template, payload_json, status, created_at)
  channel: inapp|email|sms|push
notification_deliveries(id, organization_id, notification_id, provider, provider_msg_id, status, error, attempts, sent_at, created_at)

### Analytics
fact_orders_daily(organization_id, date, orders_count, delivered_count, cancelled_count, revenue)
fact_deliveries_daily(organization_id, date, deliveries_count, delivered_count, failed_count, avg_duration_s)
fact_driver_daily(organization_id, date, driver_id, deliveries_count, distance_m, on_time_count, rating)
fact_inventory_daily(organization_id, date, product_id, warehouse_id, on_hand, reserved, low_stock_flag)
materialized views refreshed by