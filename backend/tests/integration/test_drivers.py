import uuid


def _register(client, slug=None):
    slug = slug or f"drv-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Drv Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_create_and_list_driver(client):
    tok = _register(client)
    r = client.post(
        "/api/v1/drivers",
        json={"full_name": "John Driver", "phone": "+123", "license_no": "DL1"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "offline"

    lst = client.get("/api/v1/drivers", headers=_h(tok)).json()
    assert len(lst) == 1


def test_driver_status_validation(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)
    ).json()
    r = client.patch(
        f"/api/v1/drivers/{d['id']}",
        json={"status": "bogus"},
        headers=_h(tok),
    )
    assert r.status_code == 422


def test_vehicle_flow(client):
    tok = _register(client)
    d = client.post(
        "/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)
    ).json()
    r = client.post(
        "/api/v1/drivers/vehicles",
        json={"driver_id": d["id"], "plate": "ABC123", "type": "van", "capacity_weight": "500"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    assert r.json()["type"] == "van"

    # duplicate plate
    r2 = client.post(
        "/api/v1/drivers/vehicles",
        json={"plate": "ABC123", "type": "bike"},
        headers=_h(tok),
    )
    assert r2.status_code == 409

    # invalid type
    r3 = client.post(
        "/api/v1/drivers/vehicles",
        json={"plate": "XYZ", "type": "spaceship"},
        headers=_h(tok),
    )
    assert r3.status_code == 422


def test_shift_lifecycle_and_availability(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()

    r = client.post(
        "/api/v1/drivers/shifts/start",
        json={"driver_id": d["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    shift = r.json()
    assert shift["status"] == "active"

    # driver becomes available
    d2 = client.get(f"/api/v1/drivers/{d['id']}", headers=_h(tok)).json()
    assert d2["status"] == "available"

    # double start -> 409
    r2 = client.post(
        "/api/v1/drivers/shifts/start",
        json={"driver_id": d["id"]},
        headers=_h(tok),
    )
    assert r2.status_code == 409

    # end shift
    r3 = client.post(f"/api/v1/drivers/shifts/{shift['id']}/end", headers=_h(tok))
    assert r3.status_code == 200
    assert r3.json()["status"] == "ended"

    d3 = client.get(f"/api/v1/drivers/{d['id']}", headers=_h(tok)).json()
    assert d3["status"] == "offline"


def test_record_and_fetch_position(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()

    r = client.post(
        f"/api/v1/drivers/{d['id']}/positions",
        json={"lat": 1.5, "lng": 2.5, "heading": 90, "speed": 30},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text

    latest = client.get(f"/api/v1/drivers/{d['id']}/positions/latest", headers=_h(tok)).json()
    assert latest["lat"] == 1.5

    all_pos = client.get(f"/api/v1/drivers/{d['id']}/positions", headers=_h(tok)).json()
    assert len(all_pos) == 1


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok1))
    r = client.get("/api/v1/drivers", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []