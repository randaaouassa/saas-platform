import uuid


def _register(client, slug=None):
    slug = slug or f"wh-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "WH Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_warehouse(client):
    tok = _register(client)
    r = client.post(
        "/api/v1/warehouses",
        json={"name": "Main WH", "code": "WH1", "address": "123 St", "timezone": "UTC"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    wh = r.json()
    assert wh["code"] == "WH1"

    r2 = client.get("/api/v1/warehouses", headers=_h(tok))
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_duplicate_warehouse_code(client):
    tok = _register(client)
    payload = {"name": "WH", "code": "WH1"}
    assert client.post("/api/v1/warehouses", json=payload, headers=_h(tok)).status_code == 201
    assert client.post("/api/v1/warehouses", json=payload, headers=_h(tok)).status_code == 409


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    client.post("/api/v1/warehouses", json={"name": "A", "code": "A"}, headers=_h(tok1))
    r = client.get("/api/v1/warehouses", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []


def test_zone_and_location_flow(client):
    tok = _register(client)
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": "WH1"},
        headers=_h(tok),
    ).json()

    z = client.post(
        f"/api/v1/warehouses/{wh['id']}/zones",
        json={"name": "Zone A", "code": "ZA", "type": "general"},
        headers=_h(tok),
    )
    assert z.status_code == 201, z.text
    zone = z.json()

    loc = client.post(
        f"/api/v1/warehouses/zones/{zone['id']}/locations",
        json={"code": "L1", "kind": "shelf", "capacity": 100},
        headers=_h(tok),
    )
    assert loc.status_code == 201, loc.text
    assert loc.json()["code"] == "L1"

    r = client.get(f"/api/v1/warehouses/zones/{zone['id']}/locations", headers=_h(tok))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_warehouse_task_lifecycle(client):
    tok = _register(client)
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": "WH1"},
        headers=_h(tok),
    ).json()

    t = client.post(
        "/api/v1/warehouses/tasks",
        json={"warehouse_id": wh["id"], "type": "pick", "ref_type": "order"},
        headers=_h(tok),
    )
    assert t.status_code == 201, t.text
    task = t.json()
    assert task["status"] == "pending"

    r = client.patch(
        f"/api/v1/warehouses/tasks/{task['id']}/status",
        json={"status": "in_progress"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
    assert r.json()["started_at"] is not None

    r2 = client.patch(
        f"/api/v1/warehouses/tasks/{task['id']}/status",
        json={"status": "completed"},
        headers=_h(tok),
    )
    assert r2.status_code == 200
    assert r2.json()["completed_at"] is not None


def test_task_invalid_type(client):
    tok = _register(client)
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": "WH1"},
        headers=_h(tok),
    ).json()
    r = client.post(
        "/api/v1/warehouses/tasks",
        json={"warehouse_id": wh["id"], "type": "bogus", "ref_type": "order"},
        headers=_h(tok),
    )
    assert r.status_code == 422