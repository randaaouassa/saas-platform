import uuid


def _register(client, slug=None):
    slug = slug or f"dsp-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Dsp Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make_delivery(client, tok, pickup=(1.0, 1.0)):
    return client.post(
        "/api/v1/deliveries",
        json={
            "pickup_location": "WH",
            "pickup_lat": pickup[0],
            "pickup_lng": pickup[1],
            "dropoff_location": "X",
        },
        headers=_h(tok),
    ).json()


def test_rank_returns_sorted_candidates(client):
    tok = _register(client)

    # driver near (available)
    d1 = client.post(
        "/api/v1/drivers", json={"full_name": "Near"}, headers=_h(tok)
    ).json()
    client.patch(f"/api/v1/drivers/{d1['id']}", json={"status": "available"}, headers=_h(tok))
    client.post(
        f"/api/v1/drivers/{d1['id']}/positions",
        json={"lat": 1.01, "lng": 1.01},
        headers=_h(tok),
    )

    # driver far (available)
    d2 = client.post(
        "/api/v1/drivers", json={"full_name": "Far"}, headers=_h(tok)
    ).json()
    client.patch(f"/api/v1/drivers/{d2['id']}", json={"status": "available"}, headers=_h(tok))
    client.post(
        f"/api/v1/drivers/{d2['id']}/positions",
        json={"lat": 50.0, "lng": 50.0},
        headers=_h(tok),
    )

    deliv = _make_delivery(client, tok)

    r = client.post(
        "/api/v1/dispatch/candidates",
        json={"delivery_id": deliv["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text
    cands = r.json()["candidates"]
    assert len(cands) == 2
    assert cands[0]["full_name"] == "Near"
    assert cands[0]["score"] > cands[1]["score"]


def test_auto_assign_picks_top_candidate(client):
    tok = _register(client)
    d1 = client.post("/api/v1/drivers", json={"full_name": "Near"}, headers=_h(tok)).json()
    client.patch(f"/api/v1/drivers/{d1['id']}", json={"status": "available"}, headers=_h(tok))
    client.post(
        f"/api/v1/drivers/{d1['id']}/positions",
        json={"lat": 1.0, "lng": 1.0},
        headers=_h(tok),
    )
    deliv = _make_delivery(client, tok)

    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    a = r.json()
    assert a["driver_id"] == d1["id"]
    assert a["mode"] == "auto"
    assert a["status"] == "offered"


def test_manual_assign(client):
    tok = _register(client)
    d1 = client.post("/api/v1/drivers", json={"full_name": "A"}, headers=_h(tok)).json()
    client.patch(f"/api/v1/drivers/{d1['id']}", json={"status": "available"}, headers=_h(tok))
    deliv = _make_delivery(client, tok)

    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 201
    assert r.json()["mode"] == "manual"


def test_assign_offline_driver_fails(client):
    tok = _register(client)
    d1 = client.post("/api/v1/drivers", json={"full_name": "A"}, headers=_h(tok)).json()
    # stays offline
    deliv = _make_delivery(client, tok)
    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_assign_on_assigned_delivery_fails(client):
    tok = _register(client)
    d1 = client.post("/api/v1/drivers", json={"full_name": "A"}, headers=_h(tok)).json()
    client.patch(f"/api/v1/drivers/{d1['id']}", json={"status": "available"}, headers=_h(tok))
    deliv = _make_delivery(client, tok)

    client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    # mark delivery assigned
    client.post(
        f"/api/v1/deliveries/{deliv['id']}/status",
        json={"status": "assigned"},
        headers=_h(tok),
    )

    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_assignment_status_flow(client):
    tok = _register(client)
    d1 = client.post("/api/v1/drivers", json={"full_name": "A"}, headers=_h(tok)).json()
    client.patch(f"/api/v1/drivers/{d1['id']}", json={"status": "available"}, headers=_h(tok))
    deliv = _make_delivery(client, tok)
    a = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    ).json()

    r = client.patch(
        f"/api/v1/dispatch/assignments/{a['id']}/status",
        json={"status": "accepted"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    r2 = client.patch(
        f"/api/v1/dispatch/assignments/{a['id']}/status",
        json={"status": "bogus"},
        headers=_h(tok),
    )
    assert r2.status_code == 422


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    deliv = _make_delivery(client, tok1)
    r = client.post(
        "/api/v1/dispatch/candidates",
        json={"delivery_id": deliv["id"]},
        headers=_h(tok2),
    )
    assert r.status_code == 404