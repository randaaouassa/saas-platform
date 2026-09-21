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
    u = uuid.uuid4().hex[:6]
    r = client.post(
        "/api/v1/warehouses",
        json={"name": "Main WH", "code": f"WH1{u}", "address": "123 St", "timezone": "UTC"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    wh = r.json()
    assert wh["code"] == f"WH1{u}"

    r2 = client.get("/api/v1/warehouses", headers=_h(tok))
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_duplicate_warehouse_code(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    payload = {"name": "WH", "code": f"WH1{u}"}
    assert client.post("/api/v1/warehouses", json=payload, headers=_h(tok)).status_code == 201
    assert client.post("/api/v1/warehouses", json=payload, headers=_h(tok)).status_code == 409


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    u = uuid.uuid4().hex[:6]
    client.post(
        "/api/v1/warehouses", json={"name": "A", "code": f"A{u}"}, headers=_h(tok1)
    )
    r = client.get("/api/v1/warehouses", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []


def test_zone_and_location_flow(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": f"WH1{u}"},
        headers=_h(tok),
    ).json()

    z = client.post(
        f"/api/v1/warehouses/{wh['id']}/zones",
        json={"name": "Zone A", "code": f"ZA{u}", "type": "general"},
        headers=_h(tok),
    )
    assert z.status_code == 201, z.text
    zone = z.json()

    loc = client.post(
        f"/api/v1/warehouses/zones/{zone['id']}/locations",
        json={"code": f"L1{u}", "kind": "shelf", "capacity": 100},
        headers=_h(tok),
    )
    assert loc.status_code == 201, loc.text
    assert loc.json()["code"] == f"L1{u}"

    r = client.get(f"/api/v1/warehouses/zones/{zone['id']}/locations", headers=_h(tok))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_warehouse_task_lifecycle(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": f"WH1{u}"},
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
    u = uuid.uuid4().hex[:6]
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": f"WH1{u}"},
        headers=_h(tok),
    ).json()
    r = client.post(
        "/api/v1/warehouses/tasks",
        json={"warehouse_id": wh["id"], "type": "bogus", "ref_type": "order"},
        headers=_h(tok),
    )
    assert r.status_code == 422

def test_delete_warehouse_zone_location(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    r = client.post(
        "/api/v1/warehouses", json={"name": "WH", "code": f"W{u}"}, headers=_h(tok)
    )
    assert r.status_code == 201, r.text
    wh = r.json()
    z = client.post(
        f"/api/v1/warehouses/{wh['id']}/zones",
        json={"name": "Zone", "code": f"Z{u}"},
        headers=_h(tok),
    ).json()
    loc = client.post(
        f"/api/v1/warehouses/zones/{z['id']}/locations",
        json={"code": f"L{u}"},
        headers=_h(tok),
    ).json()

    r2 = client.delete(f"/api/v1/warehouses/locations/{loc['id']}", headers=_h(tok))
    assert r2.status_code == 204
    r3 = client.delete(f"/api/v1/warehouses/zones/{z['id']}", headers=_h(tok))
    assert r3.status_code == 204
    r4 = client.delete(f"/api/v1/warehouses/{wh['id']}", headers=_h(tok))
    assert r4.status_code == 204