# ADR-0001: Multi-Tenancy Model

Status: Accepted
Date: 2025-01-01

## Context
We serve many B2B customers (organizations) from one platform. Each needs
strict data isolation. Options: database-per-tenant, schema-per-tenant,
shared-schema with `organization_id`.

## Decision
Shared database, shared schema. Every tenant-owned table has
`organization_id UUID NOT NULL` and an index leading with it. The application
layer enforces scoping; optional Postgres RLS is defense-in-depth.

## Consequences
+ Simple ops, migrations run once
+ Cheap at scale (thousands of tenants)
+ Easy cross-tenant analytics for super admins
- Requires discipline: every query must filter by `organization_id`
- Risk of leaks if a query forgets the filter → mitigated by repository layer + tests