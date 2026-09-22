# Deployment

Local dev with Docker Compose. Production on AWS (target). CI/CD via GitHub Actions.

## Environments

- **local** — developer machine, Docker Compose
- **dev** — optional shared staging on Railway/Render
- **staging** — mirror of prod, isolated data
- **prod** — customer-facing

Config is entirely env-driven. Same image runs everywhere.

## Local

Prereqs: Docker Desktop, Node 20 (for frontend only).

Setup:
  cp .env.example .env
  docker compose up -d --build
  docker compose exec api alembic upgrade head

Access:
- API         http://localhost:8000
- Docs        http://localhost:8000/docs
- Metrics     http://localhost:8000/metrics
- Frontend    http://localhost:5173
- Prometheus  http://localhost:9090
- Grafana     http://localhost:3000 (admin/admin)

Services started by `docker compose up`:
- db          postgres:16-alpine
- redis       redis:7-alpine
- api         FastAPI + uvicorn --reload
- worker      Celery worker (default, notifications, routing, analytics)
- beat        Celery beat
- outbox      domain event dispatcher loop
- prometheus  metrics scraper
- grafana     dashboards
- frontend    Vite dev server

Common commands:
  docker compose logs -f api
  docker compose exec api pytest -q
  docker compose exec api alembic revision --autogenerate -m "msg"
  docker compose exec api alembic upgrade head
  docker compose down
  docker compose down -v   # destroys data

Rebuild only one service:
  docker compose build --no-cache api
  docker compose up -d api

## Environment variables

All read from `.env` (local) or the platform's secret store (prod).

Required in prod:
- `ENV=prod`
- `DEBUG=false`
- `SECRET_KEY` (strong random)
- `POSTGRES_*`
- `REDIS_*`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `CORS_ORIGINS` (explicit, comma-separated)
- `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD`

Validation: config raises on startup if `ENV=prod` and `SECRET_KEY` is the default
or `DEBUG` is true.

Never commit `.env`. Rotate secrets at least every 90 days.

## Docker images

Backend Dockerfile (multi-stage):
- `base` — python:3.11-slim, system deps
- `dev` — installs `[dev]`, used by compose with volume mounts
- `prod` — installs only runtime deps, no volumes

Frontend Dockerfile:
- `dev` — node:20-alpine running `npm run dev`
- `build` — runs `npm run build`
- `prod` — nginx serving `dist/` with SPA fallback

Prod images should be tagged with the git SHA:
  docker build -t saas-api:$(git rev-parse --short HEAD) ./backend

## CI (GitHub Actions)

`.github/workflows/ci.yml`

Backend job:
1. Postgres + Redis service containers
2. `pip install -e ".[dev]"`
3. `ruff check app tests`
4. `pip-audit` (non-blocking)
5. `alembic upgrade head`
6. `pytest -q --cov=app --cov-fail-under=70`

Frontend job:
1. Node 20
2. `npm ci`
3. `npm run build`

Both jobs must pass before merge.

Recommended additions:
- Docker image build + push to ECR on `main`
- Deploy step (ECS update-service) gated on `main`
- Playwright E2E job
- Trivy image scan

## Production target — AWS

Topology:
- **ALB** — HTTPS terminator, public subnets
- **ECS Fargate services**
  - api (2+ tasks, autoscaling on CPU/req)
  - worker (autoscaling on queue depth)
  - beat (single task)
  - outbox (single task)
  - ws (optional separate service if scaling WS)
- **RDS Postgres 16** — Multi-AZ, private subnets
- **ElastiCache Redis** — private subnets, cluster mode off (broker + cache)
- **S3** — POD images, imports, exports
- **CloudWatch** — logs, metrics, alarms
- **Secrets Manager** — all secrets
- **ECR** — images

Networking:
- VPC with public + private subnets (2 AZs)
- Security groups: ALB → api only; api/worker → RDS/Redis; no inbound to workers

Migrations in prod:
- Run as a one-off ECS task before rollout:
  `alembic upgrade head`
- Never run migrations from app startup in prod.

Rollout:
1. Push to main
2. CI builds + pushes image tagged with SHA
3. CI runs migration task
4. CI updates ECS services
5. ALB drains old tasks; new tasks become healthy
6. Roll back by redeploying previous task definition

## Deploy checklist (prod)

Before deploy:
- CI green
- Migration reviewed and reversible
- No breaking API changes without version bump
- Feature flags set if risky
- DB backup taken (RDS automated daily + manual before big migrations)

After deploy:
- `/health/live` returns 200
- `/health/ready` returns 200
- Grafana: error rate flat, latency unchanged
- Logs: no `unhandled_error`
- Spot-check a few endpoints

## Rolling back

Fast:
- Redeploy previous task definition (ECS console or CLI)

DB:
- Migrations must be backward compatible (expand → migrate → contract pattern)
- Never drop columns in the same release that stops writing to them

Application:
- Revert the commit on main; CI deploys previous image

## Secrets

- Local: `.env` (git-ignored)
- Prod: AWS Secrets Manager → injected as ECS task env vars
- Rotate: `SECRET_KEY` (invalidates all sessions), DB password (requires coordinated restart), provider API keys

## Frontend deploy

Options:
- **Vercel** — connect the repo, set root to `frontend/`, env vars via dashboard
- **Netlify** — same idea
- **S3 + CloudFront** — `npm run build` → upload `dist/`, invalidate cache

Env vars needed:
- `VITE_API_URL` — e.g. `https://api.example.com/api/v1`
- `VITE_WS_URL` — e.g. `wss://api.example.com/ws/tracking`

CORS on the API must include the frontend origin.

## Storage — S3

Buckets:
- `saas-pod-<env>` — POD images and signatures, private
- `saas-imports-<env>` — uploaded CSVs
- `saas-exports-<env>` — generated exports

Access:
- Only from API/worker tasks via IAM role
- Presigned URLs for client download/upload

## Backups & DR

- RDS: automated daily snapshots + PITR (35 days)
- S3: versioning + cross-region replication
- Redis: not backed up (cache + broker only; use RabbitMQ/Kafka for durability at scale)
- RPO target: 5 min · RTO target: 60 min
- Quarterly restore drill

## Cost guardrails

- ECS: min 2 api tasks, min 1 worker, autoscaling cap configured
- RDS: instance sized from observed p95 + 50% headroom
- CloudWatch log retention 30 days hot, then archive
- S3 lifecycle: objects > 90 days to Glacier

## Anti-patterns

- Running migrations on app boot in prod
- Baking secrets into images
- `docker compose up` in prod
- `--privileged` containers
- Public RDS / Redis
- Wildcard CORS in prod
- Committing `.env`