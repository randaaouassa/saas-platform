# Onboarding

New engineer, day 1 to first PR.

## Day 1 — Get it running

1. Install Docker Desktop.
2. Clone the repository.
3. From the repo root:
   cp .env.example .env
   docker compose up -d --build
   docker compose exec api alembic upgrade head

4. Verify:
   curl http://localhost:8000/health/live
   → {"status":"ok"}

5. Open:
   - API docs     http://localhost:8000/docs
   - Frontend     http://localhost:5173
   - Grafana      http://localhost:3000 (admin/admin)

6. Register a workspace at `/register`. You become `org_admin`.
   Use a fresh slug (e.g. `dev-yourname`) so you don't collide with others.

## Day 1 — Read these, in order

1. `README.md`
2. `docs/01-architecture.md`
3. `docs/02-erd.md`
4. `docs/04-backend.md`
5. `docs/05-frontend.md`
6. `docs/08-testing.md`

Optional later:
- `docs/06-ui-ux.md` — design system
- `docs/07-api.md` — REST catalog
- `docs/09-observability.md`
- `docs/10-runbook.md`
- `docs/11-deployment.md`

## Day 2 — Explore

Backend:
- `backend/app/main.py` — entrypoint, routers
- `backend/app/core/` — the foundation (config, db, uow, security, errors)
- Pick a module: `backend/app/modules/orders/` and read all 4 files.

Frontend:
- `frontend/src/main.tsx` and `App.tsx` — routes and providers
- `frontend/src/app/` — role-based layouts
- Pick a feature: `frontend/src/features/orders/` — list + detail.

Run the tests:
  docker compose exec api pytest -q

Break something and watch it fail — that's the best way to learn the system.

## Day 3 — Ship a small change

Choose one:
- Add a field to a detail page
- Add a filter to a list page
- Add one integration test for an endpoint

Workflow:
1. `git checkout -b feat/your-change`
2. Make the change.
3. Run `ruff check app tests` and `pytest -q` locally.
4. Run `npm run build` if you touched the frontend.
5. Commit with a conventional message:
   feat(orders): add paid status filter
6. Push and open a PR.

## Repository map

- `backend/` — FastAPI service
  - `app/core/` — cross-cutting concerns
  - `app/shared/` — mixins, pagination, filters
  - `app/modules/<domain>/` — bounded contexts
  - `alembic/` — migrations
  - `tests/` — unit + integration
- `frontend/` — React app
  - `src/app/` — layouts + routing
  - `src/features/<domain>/` — pages per domain
  - `src/shared/` — API client, stores, components
- `docs/` — everything you're reading
- `infra/` — observability configs
- `.github/workflows/` — CI

## Local dev loop

Backend (auto-reloads on save):
  docker compose logs -f api

Run a single test:
  docker compose exec api pytest tests/integration/test_orders.py::test_create_customer_and_order -v

Create a migration after changing a model:
  docker compose exec api alembic revision --autogenerate -m "add x"
  docker compose exec api alembic upgrade head

Roll back the last migration:
  docker compose exec api alembic downgrade -1

Frontend:
  cd frontend
  npm install
  npm run dev

The frontend calls the API at `http://localhost:8000` by default
(see `frontend/src/shared/lib/config.ts`). The API allows `localhost:5173` and
`localhost:5174` in CORS by default.

## Conventions

- One concept per module. Don't cross domains in a service.
- Routers are thin. Services do the work. Models don't know about HTTP.
- Never open a DB session manually in a service — use the injected `uow`.
- Every state change writes an audit row and emits a domain event.
- Every list page on the frontend needs a skeleton, a search, an empty state.
- Every status shown in the UI goes through `<StatusBadge domain="..." />`.
- Ruff line length is 120. Type hints everywhere.

## PR checklist

- [ ] Tests pass locally (`pytest -q`)
- [ ] Ruff clean (`ruff check app tests`)
- [ ] Frontend builds (`npm run build`) if touched
- [ ] Migration included if models changed
- [ ] Docs updated if behavior changed
- [ ] No secrets committed
- [ ] Conventional commit message

## Debugging tips

- "Missing table" → run migrations
- "CORS error" → add the frontend origin to `CORS_ORIGINS`, restart api
- "401 everywhere" → clear localStorage `auth` key, log in again
- "WS Offline" → check the token hasn't expired, check the outbox container is up
- "Tests fail with unique constraint" → use a unique slug in your test helper
- "Invite fails" → token returned once at creation; regenerate

## Getting help

- Search the docs first.
- For runtime errors: check `docker compose logs <service> --tail=100`.
- For DB state: `docker compose exec db psql -U postgres -d saas_platform`.
- For metrics: open Grafana Overview dashboard.
- For API shapes: open `/docs`.

## First-week goal

By the end of week 1 you should be able to:
- Explain the multi-tenancy model
- Explain the outbox pattern used here
- Add a new endpoint with a migration and a test
- Ship a frontend page that talks to it