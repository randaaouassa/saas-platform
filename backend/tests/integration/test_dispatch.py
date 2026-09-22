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


def _make_delivery(client, tok, pickup=(1.0, 1.0), packages=None):
    payload = {
        "pickup_location": "WH",
        "pickup_lat": pickup[0],
        "pickup_lng": pickup[1],
        "dropoff_location": "X",
    }
    if packages:
        payload["packages"] = packages
    return client.post("/api/v1/deliveries", json=payload, headers=_h(tok)).json()


def _make_driver(client, tok, name, lat, lng, vehicle_weight=None, u=None):
    d = client.post(
        "/api/v1/drivers", json={"full_name": name}, headers=_h(tok)
    ).json()
    client.patch(f"/api/v1/drivers/{d['id']}", json={"status": "available"}, headers=_h(tok))
    client.post(
        f"/api/v1/drivers/{d['id']}/positions",
        json={"lat": lat, "lng": lng},
        headers=_h(tok),
    )
    if vehicle_weight is not None:
        v = client.post(
            "/api/v1/drivers/vehicles",
            json={
                "driver_id": d["id"],
                "plate": f"P{u}-{name[:3]}",
                "type": "van",
                "capacity_weight": str(vehicle_weight),
            },
            headers=_h(tok),
        ).json()
        return d, v
    return d, None


def test_rank_returns_sorted_candidates(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    _make_driver(client, tok, "Near", 1.01, 1.01, u=u)
    _make_driver(client, tok, "Far", 50.0, 50.0, u=u)
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


def test_capacity_affects_score(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    # small van can't carry 100kg package
    _make_driver(client, tok, "Small", 1.0, 1.0, vehicle_weight=5, u=u)
    # big truck
    _make_driver(client, tok, "Big", 1.0, 1.0, vehicle_weight=1000, u=u)

    deliv = _make_delivery(
        client, tok,
        packages=[{"code": f"PKG-{u}", "weight": "100"}],
    )

    r = client.post(
        "/api/v1/dispatch/candidates",
        json={"delivery_id": deliv["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 200
    cands = {c["full_name"]: c for c in r.json()["candidates"]}
    assert cands["Small"]["capacity_ok"] is False
    assert cands["Big"]["capacity_ok"] is True
    assert cands["Big"]["score"] > cands["Small"]["score"]


def test_auto_assign_picks_top_candidate(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "Near", 1.0, 1.0, u=u)
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
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "A", 1.0, 1.0, u=u)
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
    d1 = client.post(
        "/api/v1/drivers", json={"full_name": "A"}, headers=_h(tok)
    ).json()
    deliv = _make_delivery(client, tok)
    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_double_assign_fails(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "A", 1.0, 1.0, u=u)
    deliv = _make_delivery(client, tok)

    client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    r = client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_reassign(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "A", 1.0, 1.0, u=u)
    d2, _ = _make_driver(client, tok, "B", 2.0, 2.0, u=u)
    deliv = _make_delivery(client, tok)

    client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )

    r = client.post(
        "/api/v1/dispatch/reassign",
        json={
            "delivery_id": deliv["id"],
            "new_driver_id": d2["id"],
            "reason": "closer",
        },
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text
    assert r.json()["driver_id"] == d2["id"]

    active = client.get(
        f"/api/v1/dispatch/assignments?delivery_id={deliv['id']}", headers=_h(tok)
    ).json()
    offered = [a for a in active if a["status"] == "offered"]
    rejected = [a for a in active if a["status"] == "rejected"]
    assert len(offered) == 1
    assert len(rejected) == 1


def test_unassign(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "A", 1.0, 1.0, u=u)
    deliv = _make_delivery(client, tok)
    client.post(
        "/api/v1/dispatch/assign",
        json={"delivery_id": deliv["id"], "driver_id": d1["id"]},
        headers=_h(tok),
    )

    r = client.post(
        "/api/v1/dispatch/unassign",
        json={"delivery_id": deliv["id"], "reason": "change"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["unassigned"] == 1


def test_assignment_status_flow(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    d1, _ = _make_driver(client, tok, "A", 1.0, 1.0, u=u)
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