import uuid


def _register(client, slug=None):
    slug = slug or f"ntf-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Ntf Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()
    return data["access_token"], data


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_create_inapp_notification(client):
    tok, _ = _register(client)
    r = client.post(
        "/api/v1/notifications",
        json={"channel": "inapp", "template": "welcome", "payload": {"x": 1}},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    n = r.json()
    assert n["status"] == "sent"
    assert n["channel"] == "inapp"


def test_create_email_notification_creates_delivery(client):
    tok, _ = _register(client)
    r = client.post(
        "/api/v1/notifications",
        json={"channel": "email", "template": "order.shipped", "payload": {"order": "1"}},
        headers=_h(tok),
    )
    assert r.status_code == 201
    n = r.json()
    assert n["status"] == "queued"

    dels = client.get(
        f"/api/v1/notifications/{n['id']}/deliveries", headers=_h(tok)
    ).json()
    assert len(dels) == 1
    assert dels[0]["provider"] == "email"
    assert dels[0]["status"] == "pending"


def test_invalid_channel(client):
    tok, _ = _register(client)
    r = client.post(
        "/api/v1/notifications",
        json={"channel": "pigeon", "template": "x"},
        headers=_h(tok),
    )
    assert r.status_code == 422


def test_mark_read_and_read_all(client):
    tok, data = _register(client)
    me_id = None
    me = client.get("/api/v1/auth/me", headers=_h(tok)).json()
    me_id = me["id"]

    for _ in range(3):
        client.post(
            "/api/v1/notifications",
            json={"channel": "inapp", "template": "t", "user_id": me_id},
            headers=_h(tok),
        )

    unread = client.get("/api/v1/notifications/mine?unread_only=true", headers=_h(tok)).json()
    assert len(unread) == 3

    n_id = unread[0]["id"]
    r = client.post(f"/api/v1/notifications/{n_id}/read", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["read_at"] is not None

    r2 = client.post("/api/v1/notifications/mine/read-all", headers=_h(tok))
    assert r2.status_code == 200
    assert r2.json()["marked"] == 2

    unread2 = client.get("/api/v1/notifications/mine?unread_only=true", headers=_h(tok)).json()
    assert len(unread2) == 0


def test_tenant_isolation(client):
    tok1, _ = _register(client)
    tok2, _ = _register(client)
    client.post(
        "/api/v1/notifications",
        json={"channel": "inapp", "template": "t"},
        headers=_h(tok1),
    )
    r = client.get("/api/v1/notifications", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []