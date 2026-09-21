import uuid


def _register(client, slug=None):
    slug = slug or f"del-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Del Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_create_delivery_with_packages(client):
    tok = _register(client)
    r = client.post(
        "/api/v1/deliveries",
        json={
            "dropoff_location": "1 Main St",
            "dropoff_lat": 1.0,
            "dropoff_lng": 2.0,
            "packages": [{"code": "PKG-1", "weight": "1.5"}],
        },
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["status"] == "pending"
    assert len(d["packages"]) == 1


def test_duplicate_package_code(client):
    tok = _register(client)
    payload = {
        "dropoff_location": "X",
        "packages": [{"code": "PKG-1"}],
    }
    assert client.post("/api/v1/deliveries", json=payload, headers=_h(tok)).status_code == 201
    assert client.post("/api/v1/deliveries", json=payload, headers=_h(tok)).status_code == 409


def test_delivery_lifecycle(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "1 Main St"},
        headers=_h(tok),
    ).json()

    for s in ["assigned", "picked_up", "in_transit", "delivered"]:
        r = client.post(
            f"/api/v1/deliveries/{d['id']}/status",
            json={"status": s},
            headers=_h(tok),
        )
        assert r.status_code == 200, (s, r.text)

    final = client.get(f"/api/v1/deliveries/{d['id']}", headers=_h(tok)).json()
    assert final["status"] == "delivered"
    assert final["delivered_at"] is not None


def test_invalid_transition(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/deliveries/{d['id']}/status",
        json={"status": "delivered"},
        headers=_h(tok),
    )
    assert r.status_code == 422


def test_failed_requires_reason(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()
    client.post(f"/api/v1/deliveries/{d['id']}/status", json={"status": "assigned"}, headers=_h(tok))
    client.post(f"/api/v1/deliveries/{d['id']}/status", json={"status": "picked_up"}, headers=_h(tok))

    r = client.post(
        f"/api/v1/deliveries/{d['id']}/status",
        json={"status": "failed"},
        headers=_h(tok),
    )
    assert r.status_code == 422

    r2 = client.post(
        f"/api/v1/deliveries/{d['id']}/status",
        json={"status": "failed", "failed_reason": "customer absent"},
        headers=_h(tok),
    )
    assert r2.status_code == 200
    assert r2.json()["failed_reason"] == "customer absent"


def test_history(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()
    client.post(f"/api/v1/deliveries/{d['id']}/status", json={"status": "assigned"}, headers=_h(tok))

    r = client.get(f"/api/v1/deliveries/{d['id']}/history", headers=_h(tok))
    assert r.status_code == 200
    hist = r.json()
    assert len(hist) == 2
    assert hist[0]["to_status"] == "pending"
    assert hist[1]["to_status"] == "assigned"


def test_pod(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/deliveries/{d['id']}/pod",
        json={"kind": "photo", "s3_key": "pod/123.jpg", "signer_name": "Jane"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    assert r.json()["kind"] == "photo"

    r2 = client.get(f"/api/v1/deliveries/{d['id']}/pod", headers=_h(tok))
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok1),
    )
    r = client.get("/api/v1/deliveries", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []