import uuid

import pytest
from starlette.websockets import WebSocketDisconnect


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


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_ws_rejects_bad_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/tracking?token=bad") as ws:
            ws.receive_text()


def test_ws_accepts_valid_token(client):
    tok = _register(client)
    with client.websocket_connect(f"/ws/tracking?token={tok}&topics=delivery") as ws:
        ws.send_text("ping")


def test_tracking_events_recorded_on_transition(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()

    client.post(
        f"/api/v1/deliveries/{d['id']}/status",
        json={"status": "assigned"},
        headers=_h(tok),
    )

    r = client.get(
        f"/api/v1/tracking/deliveries/{d['id']}/events", headers=_h(tok)
    )
    assert r.status_code == 200
    events = r.json()
    types = [e["type"] for e in events]
    assert "pending" in types
    assert "assigned" in types


def test_public_tracking(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "Main St", "dropoff_lat": 1.0, "dropoff_lng": 2.0},
        headers=_h(tok),
    ).json()
    token = d["public_token"]
    assert token

    r = client.get(f"/api/v1/public/track/{token}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["dropoff_location"] == "Main St"
    assert len(body["history"]) >= 1


def test_public_tracking_unknown(client):
    r = client.get("/api/v1/public/track/does-not-exist")
    assert r.status_code == 404


def test_public_tracking_after_transitions(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "Y"},
        headers=_h(tok),
    ).json()
    token = d["public_token"]

    for s in ["assigned", "picked_up", "in_transit", "delivered"]:
        client.post(
            f"/api/v1/deliveries/{d['id']}/status",
            json={"status": s},
            headers=_h(tok),
        )

    r = client.get(f"/api/v1/public/track/{token}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "delivered"
    assert body["delivered_at"] is not None
    types = [e["type"] for e in body["history"]]
    assert "delivered" in types