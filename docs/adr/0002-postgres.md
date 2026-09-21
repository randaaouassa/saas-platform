# ADR-0002: PostgreSQL as Primary Datastore

Status: Accepted

## Context
Need a relational store with strong consistency, JSON support, transactions,
spatial queries (driver search), and mature tooling.

## Decision
PostgreSQL 16.

## Consequences
+ ACID, rich types (JSONB, UUID, timestamptz, numeric)
+ PostGIS for geo queries
+ Partitioning, materialized views, logical replication
+ First-class support in SQLAlchemy / Alembic
- Vertical scaling limit → addressed with replicas + partitioning