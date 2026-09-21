import uuid

import pytest


def _register(client, slug=None):
    slug = slug or f"trk-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Trk Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def test_ws_rejects_bad_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/tracking?token=bad") as ws:
            ws.receive_text()


def test_ws_accepts_valid_token(client):
    tok = _register(client)
    with client.websocket_connect(f"/ws/tracking?token={tok}&topics=delivery") as ws:
        ws.send_text("ping")