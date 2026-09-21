import uuid
from datetime import date


def _register(client, slug=None):
    slug = slug or f"rt-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Rt Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _mk_delivery(client, tok, lat, lng):
    return client.post(
        "/api/v1/deliveries",
        json={
            "pickup_location": "WH",
            "pickup_lat": 0.0,
            "pickup_lng": 0.0,
            "dropoff_location": "X",
            "dropoff_lat": lat,
            "dropoff_lng": lng,
        },
        headers=_h(tok),
    ).json()


def test_create_route_orders_stops(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()

    # far first, near second — nearest-neighbor should reorder so near is first
    far = _mk_delivery(client, tok, 50.0, 50.0)
    near = _mk_delivery(client, tok, 0.1, 0.1)

    r = client.post(
        "/api/v1/routes",
        json={
            "driver_id": d["id"],
            "date": date.today().isoformat(),
            "delivery_ids": [far["id"], near["id"]],
        },
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    route = r.json()
    assert len(route["stops"]) == 2
    assert route["stops"][0]["delivery_id"] == near["id"]
    assert route["total_distance_m"] is not None


def test_route_status_flow(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()
    deliv = _mk_delivery(client, tok, 1.0, 1.0)

    route = client.post(
        "/api/v1/routes",
        json={"driver_id": d["id"], "date": date.today().isoformat(), "delivery_ids": [deliv["id"]]},
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/routes/{route['id']}/status?status_value=active",
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    r2 = client.post(
        f"/api/v1/routes/{route['id']}/status?status_value=bogus",
        headers=_h(tok),
    )
    assert r2.status_code == 422


def test_stop_status_updates(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()
    deliv = _mk_delivery(client, tok, 1.0, 1.0)
    route = client.post(
        "/api/v1/routes",
        json={"driver_id": d["id"], "date": date.today().isoformat(), "delivery_ids": [deliv["id"]]},
        headers=_h(tok),
    ).json()
    stop = route["stops"][0]

    r = client.patch(
        f"/api/v1/routes/stops/{stop['id']}/status",
        json={"status": "arrived"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "arrived"
    assert r.json()["arrived_at"] is not None

    r2 = client.patch(
        f"/api/v1/routes/stops/{stop['id']}/status",
        json={"status": "completed"},
        headers=_h(tok),
    )
    assert r2.status_code == 200
    assert r2.json()["departed_at"] is not None


def test_recalculate_reorders_pending(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()

    a = _mk_delivery(client, tok, 10.0, 10.0)
    b = _mk_delivery(client, tok, 0.5, 0.5)
    c = _mk_delivery(client, tok, 20.0, 20.0)

    route = client.post(
        "/api/v1/routes",
        json={
            "driver_id": d["id"],
            "date": date.today().isoformat(),
            "delivery_ids": [a["id"], b["id"], c["id"]],
        },
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/routes/{route['id']}/recalculate",
        json={"reason": "traffic"},
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text

    recalc = client.get(
        f"/api/v1/routes/{route['id']}/recalculations", headers=_h(tok)
    ).json()
    assert len(recalc) == 1
    assert recalc[0]["reason"] == "traffic"


def test_recalculate_needs_pending_stops(client):
    tok = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok)).json()
    deliv = _mk_delivery(client, tok, 1.0, 1.0)
    route = client.post(
        "/api/v1/routes",
        json={"driver_id": d["id"], "date": date.today().isoformat(), "delivery_ids": [deliv["id"]]},
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/routes/{route['id']}/recalculate",
        json={"reason": "x"},
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    d = client.post("/api/v1/drivers", json={"full_name": "J"}, headers=_h(tok1)).json()
    deliv = _mk_delivery(client, tok1, 1.0, 1.0)
    client.post(
        "/api/v1/routes",
        json={"driver_id": d["id"], "date": date.today().isoformat(), "delivery_ids": [deliv["id"]]},
        headers=_h(tok1),
    )
    r = client.get("/api/v1/routes", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []