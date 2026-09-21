import json
import uuid

from fastapi.testclient import TestClient


def test_missing_key_passes_through(client, org_payload):
    # normal register without idempotency-key works
    r = client.post("/api/v1/auth/register", json=org_payload)
    assert r.status_code == 201


def test_same_key_returns_cached_response(client, org_payload):
    key = uuid.uuid4().hex
    payload = {
        "organization": {"name": "Idem Co", "slug": f"idem-{uuid.uuid4().hex[:6]}"},
        "email": f"admin-{uuid.uuid4().hex[:6]}@idem.com",
        "password": "password123",
        "full_name": "Admin",
    }
    r1 = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    assert r2.status_code == 201
    assert r2.headers.get("x-idempotent-replay") == "true"
    assert r1.json() == r2.json()