# ADR-0003: JWT Auth with Rotating Refresh Tokens

Status: Accepted

## Context
Stateless API, multiple clients (web, mobile future). Need short-lived
credentials and revocable sessions.

## Decision
- Access token: JWT, 15 min TTL, carries `sub`, `org`, `roles`, `jti`.
- Refresh token: JWT, 7 days TTL, single-use, rotating, stored hashed in DB.
- Reuse detection revokes the entire session family.

## Consequences
+ Stateless access checks (no DB hit per request beyond user lookup)
+ Revocable via refresh table
+ Short blast radius if access token leaks
- Refresh token management adds DB writes
- Clock skew needs tolerance (leeway)