# Threat Model (STRIDE)

Scope: API + data plane. Updated as architecture evolves.

## Assets
- Tenant data (orders, inventory, drivers, customers)
- Credentials (password hashes, refresh tokens, secrets)
- PII (customer names, phones, addresses)
- POD images / signatures
- Audit log

## Trust Boundaries
- Client ↔ API (public)
- API ↔ Postgres/Redis (private)
- API/Workers ↔ External providers (email, SMS, maps)
- Super Admin ↔ tenant data (privileged cross-tenant)

## Threats & Mitigations

### Spoofing
- Password auth: bcrypt(12), lockout via rate limits, optional MFA.
- Tokens: signed JWT, `jti`, short TTL, rotating refresh, reuse detection.
- WS: token-in-handshake, per-connection identity.

### Tampering
- TLS everywhere.
- Pydantic input validation on every endpoint.
- ORM/parameterized queries only.
- Signed webhooks (future) with HMAC.
- Immutable audit log (append-only).

### Repudiation
- Audit log for privileged actions with actor, ip, ua, ts.
- Request-ID propagated end to end.

### Information Disclosure
- Tenant isolation via `organization_id` + repository + tests.
- PII masked in logs (planned helper).
- Errors return RFC 7807 without stack traces in prod.
- Secrets in env / Secrets Manager, never in code.
- Encryption at rest (RDS, S3, EBS).

### Denial of Service
- Rate limiting per IP + per user (Redis token bucket).
- Request body size caps (proxy + app).
- Bounded queues; DLQ on overflow.
- WS backpressure: per-connection rate limit, drop slow consumers.
- DB connection pool caps.

### Elevation of Privilege
- RBAC: permissions `<resource>:<action>`, deny by default.
- Route guard + service guard (belt and suspenders).
- No cross-tenant queries outside super_admin.
- Postgres RLS (optional, defense-in-depth).
- Principle of least privilege for DB and IAM roles.

## Residual Risks
- Compromised super_admin account → mitigated by MFA + audit.
- Leaked refresh token before rotation → mitigated by reuse detection.
- Third-party routing provider outage → cached fallback.

## Review Cadence
Quarterly, or on architecture change.