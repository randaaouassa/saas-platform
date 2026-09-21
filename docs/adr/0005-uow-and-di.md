# ADR-0005: Unit of Work + FastAPI DI

Status: Accepted

## Context
Transactions must be explicit and testable; services shouldn’t reach into
globals.

## Decision
- `UnitOfWork` wraps a session and exposes `commit/rollback/flush`.
- FastAPI `Depends(get_uow)` injects it per request.
- Services accept `uow` as a parameter, never build sessions themselves.

## Consequences
+ One transaction per request by default
+ Swappable in tests (override dependency)
+ Clear boundaries for services
- Slight boilerplate in every service signature