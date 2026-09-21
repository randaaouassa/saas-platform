# ADR-0004: Celery for Background Jobs

Status: Accepted

## Context
Long-running and external work (notifications, route optimization,
analytics rollups) must not block HTTP requests.

## Decision
Celery with Redis broker. Dedicated queues: default, notifications, routing,
analytics. Retries with exponential backoff, DLQ after N attempts.

## Consequences
+ Mature, widely deployed
+ Per-queue workers scale independently
+ Task routing by name
- Redis broker not durable at extreme scale → migrate to RabbitMQ/Kafka later if needed
- Ops overhead (workers, beat, monitoring)