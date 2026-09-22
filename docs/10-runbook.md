# Runbook

On-call playbook. Every alert has an action. Every action is safe to run.

## Severity levels

- **SEV1** — customer-facing outage (API down, DB down, data loss)
- **SEV2** — degraded (elevated 5xx, latency spikes, one queue stalled)
- **SEV3** — single component failing (a worker, a dashboard, a background job)

## Golden signals

- Availability (up %)
- Latency (p95)
- Error rate (5xx %)
- Saturation (DB connections, queue depth)

## Quick diagnostics

Check everything at once:
  docker compose ps
  curl -s localhost:8000/health/live
  curl -s localhost:8000/health/ready
  curl -s localhost:8000/metrics | head -40

Logs:
  docker compose logs api --tail=100
  docker compose logs worker --tail=100
  docker compose logs outbox --tail=100

Recent errors across services:
  docker compose logs --since=15m | grep -i error

## Alert: ApiDown

Signal: `up{job="api"} == 0` for 1m.

Steps:
1. `docker compose ps api`
2. If not running: `docker compose up -d api` and watch logs.
3. If crash-looping: `docker compose logs api --tail=200`.
   Common causes:
   - Migration missing → `docker compose exec api alembic upgrade head`
   - Bad env → check `.env` against `.env.example`
   - DB unreachable → check `db` container + `POSTGRES_*` vars
4. If running but health fails: check `/health/live` and DB connectivity.
5. Post-incident: note the cause in `docs/14-changelog.md`.

## Alert: HighErrorRate (5xx > 1%)

Signal: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01`.

Steps:
1. `docker compose logs api --since=10m | grep -i "unhandled\|traceback"`.
2. Identify the endpoint from the logs (path label) or Grafana → API dashboard.
3. Reproduce: `curl -v <endpoint>`.
4. If DB error → check `db` logs, look for lock contention, missing table, connection limit.
5. If Redis error → check `redis` container; rate limiting and pub/sub degrade gracefully.
6. If code error → fix, redeploy.

## Alert: HighLatencyP95 (p95 > 400ms)

Signal: `histogram_quantile(0.95, ...) > 0.4` for 10m.

Steps:
1. Grafana → API dashboard → find the slow path.
2. Check DB: `docker compose exec db psql -U postgres -d saas_platform -c "SELECT pid, query, state, wait_event_type FROM pg_stat_activity WHERE state != 'idle';"`
3. Check pool saturation: number of active connections vs. pool size (10 + 20 overflow).
4. Slow queries → add indexes; use `EXPLAIN ANALYZE`.
5. If Redis is slow: `docker compose exec redis redis-cli --latency`.
6. If external calls are slow: check maps/routing provider latency.

## Alert: Outbox lag > 30s

Signal: `domain_events_unpublished_total > 0` sustained.

Steps:
1. `docker compose logs outbox --tail=100`.
2. If worker is not running: `docker compose up -d outbox`.
3. If worker is erroring on publish: check `redis` container.
4. If events are stuck due to consumer failure: check `events.dispatcher` logs for
   `event_consumer_failed`.
5. Manual replay is safe — the worker retries every second.

## Alert: DLQ depth > 0

Signal: `dlq` queue length > 0.

Steps:
1. Inspect: `docker compose exec worker celery -A app.core.celery_app inspect active_queues`.
2. Look at recent errors in worker logs.
3. Replay via the DLQ task: `default.dlq_replay`.
4. If a task is fundamentally broken, disable it and open a ticket.

## Alert: DB connections exhausted

Symptom: API errors `remaining connection slots are reserved`.

Steps:
1. `docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"`
2. `SELECT pid, state, query FROM pg_stat_activity WHERE state != 'idle';`
3. Kill long idle-in-transaction: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - state_change > interval '5 minutes';`
4. Restart api to reset pool: `docker compose restart api`.
5. Long term: raise `pool_size` or add PgBouncer.

## Alert: Redis down

Symptom: rate limit bypass logs, WS disconnects, outbox publish failures.

Steps:
1. `docker compose ps redis`
2. `docker compose exec redis redis-cli ping`
3. Restart: `docker compose restart redis`
4. API continues (rate limit and idempotency degrade gracefully).
5. WS clients reconnect automatically with backoff.

## Scenario: Migration failure

Steps:
1. `docker compose exec api alembic current`
2. `docker compose exec api alembic history | head`
3. If DB is partially migrated:
   - For local: `docker compose down -v` (destroys data)
   - For prod: hand-craft a fix migration, do not drop data
4. Never edit a migration already applied in any environment.

## Scenario: Suspend or resume an org

Only super_admin can.

PATCH /api/v1/system/orgs/{id}/status
  body: {"status": "suspended"}

Suspended orgs cannot authenticate (login rejects with "invalid credentials").

## Scenario: Super admin locked out

1. Check `.env` for `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD`.
2. If missing, set them and restart api: `docker compose restart api`.
3. Bootstrap runs on every startup and creates the account if it doesn't exist.
4. If it exists but password is unknown:
   - Reset via SQL (dev only):
     DELETE FROM users WHERE email = '<super admin email>' AND organization_id = (SELECT id FROM organizations WHERE slug='platform');
   - Restart api — bootstrap recreates.

## Scenario: Password reset link not arriving

In dev, the token is returned directly from `/auth/forgot-password`.
In prod, plug in an email provider (`app/modules/notifications/providers.py`).

## Scenario: Rate limit false positive in dev

Set `RATE_LIMIT_ENABLED=false` in `.env`, restart api.

## Scenario: WS not updating

1. Check the top-right dot in the UI. If Offline → token expired or WS closed.
2. `docker compose logs api | grep tracking.ws`
3. Check that `outbox` is running and publishing events.
4. Verify the org in the JWT matches the events being emitted.

## Standard recovery commands

Restart one service:
  docker compose restart api

Restart everything:
  docker compose restart

Full reset (DEV ONLY, destroys DB):
  docker compose down -v
  docker compose up -d
  docker compose exec api alembic upgrade head

Run migrations:
  docker compose exec api alembic upgrade head

Rollback one migration:
  docker compose exec api alembic downgrade -1

Run tests:
  docker compose exec api pytest -q

## Post-incident

- Record the incident in `docs/14-changelog.md` under "Incidents"
- Add or update an alert if the failure was silent
- Add a test if the failure was preventable
- Add a runbook entry if the resolution was non-obvious