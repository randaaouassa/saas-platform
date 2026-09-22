# Changelog

All notable changes to this project. Format based on Keep a Changelog.
Versioning follows Semantic Versioning once we hit 1.0.0.

## [Unreleased]

### Added
- Landing page with feature grid
- Frontend README badges
- Docs: backend reference, frontend guide, UI/UX system, API reference,
  testing strategy, observability, runbook, deployment, onboarding, glossary,
  contributing

### Changed
- README rewritten with full system overview

### Fixed
- Invitation accept now returns a token pair (auto-login)
- Invitation validate endpoint surfaces org name, slug, and role
- Accept invite auto-creates a Driver profile when role is `driver`
- CORS default includes `localhost:5174`

## [0.1.0] — Initial foundation

### Added

**Core**
- Config, DB, UoW, security (bcrypt + JWT), logging (structlog),
  errors (RFC 7807), metrics (Prometheus), OpenTelemetry hooks
- Request ID middleware, idempotency middleware, rate limit middleware
- Audit log, transactional outbox with dispatcher worker
- Celery app with queues, DLQ hook, beat schedule, cleanup tasks
- Super admin bootstrap

**Modules**
- Identity: organizations, users, roles, permissions, sessions,
  invitations, password reset, users CRUD, roles assign/revoke
- Warehouse: warehouses, zones, locations, tasks (receiving/pick/pack/transfer/adjust)
- Inventory: products, stock, movements, reservations, alerts, transfers, low-stock scan
- Orders: customers, orders, items, lifecycle, cancel, CSV import
- Deliveries: deliveries, packages, status, POD, cancel, reschedule, public token
- Drivers: profiles, vehicles, shifts, positions, `/drivers/me`
- Dispatch: candidate ranking (distance + workload + capacity), assign,
  reassign, unassign, auto-dispatch task
- Routing: routes, stops, nearest-neighbor ordering, add/remove stop,
  start/complete, recalculation, real ETA
- Tracking: WebSocket endpoint with Redis pub/sub fanout, tracking events,
  public tracking endpoint
- Notifications: templates, providers, auto-trigger from domain events,
  worker task
- Analytics: daily facts, rebuild, range queries, average delivery time,
  top products, CSV exports
- System: version, tenant stats, org list + suspend, super_admin gated

**Database**
- Full Alembic migration history for every module
- All tables carry `organization_id` for tenant isolation
- Indexes on all foreign keys and hot-path columns

**Frontend**
- Apple-inspired dark theme with purple accent and pastel statuses
- Landing, Login, Register, Accept Invite, Public Tracking
- Role-based layouts: admin, dispatcher, driver, warehouse
- Pages: Dashboard, Analytics, Warehouses, Inventory, Orders (+detail),
  Deliveries (+detail), Drivers (+detail), Dispatch (with live map), Routing,
  Notifications, Users, Settings
- WebSocket live indicator, React Query, Zustand stores, Axios JWT refresh
- Skeleton screens, top progress bar, toasts, filters, search, empty states
- Leaflet maps for dispatch and tracking
- Recharts for analytics

**Infra**
- Docker Compose with 10 services
- Prometheus + Grafana provisioned
- GitHub Actions CI: ruff → pip-audit → alembic → pytest (coverage gate 70%)
  + frontend build

**Tests**
- 139 tests: unit (security, pagination, filters, scoring, haversine,
  rate limits, celery config) + integration (all modules)

**Docs**
- README, architecture, ERD, roadmap, 5 ADRs, threat model

---

## Incidents

_None recorded yet._

When an incident occurs, add an entry here with:
- Date
- Severity (SEV1/2/3)
- Impact
- Root cause
- Resolution
- Follow-up actions

---

## Release process

1. Update this changelog under `[Unreleased]` as you work.
2. On release: move entries to a new version section with today's date.
3. Tag the commit: `git tag -a v0.2.0 -m "v0.2.0"` and push the tag.
4. Attach release notes on GitHub from this file.

## Format

Sections: Added, Changed, Deprecated, Removed, Fixed, Security.
Order newest first. Every user-visible change gets an entry.