import uuid


def _register(client, slug=None):
    slug = slug or f"inv-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Inv Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _setup_wh(client, tok):
    return client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": "WH1"},
        headers=_h(tok),
    ).json()


def test_create_product_and_duplicate(client):
    tok = _register(client)
    payload = {"sku": "SKU1", "name": "Widget"}
    r = client.post("/api/v1/inventory/products", json=payload, headers=_h(tok))
    assert r.status_code == 201, r.text
    assert r.json()["sku"] == "SKU1"

    r2 = client.post("/api/v1/inventory/products", json=payload, headers=_h(tok))
    assert r2.status_code == 409


def test_receive_stock_and_list(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()

    r = client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "100"},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    assert float(r.json()["quantity"]) == 100.0

    r2 = client.get("/api/v1/inventory/stock", headers=_h(tok))
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_adjust_stock_cannot_go_negative(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()

    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "10"},
        headers=_h(tok),
    )

    r = client.post(
        "/api/v1/inventory/stock/adjust",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "-20"},
        headers=_h(tok),
    )
    assert r.status_code == 422


def test_reservation_lifecycle(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()
    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "50"},
        headers=_h(tok),
    )

    order_id = str(uuid.uuid4())
    r = client.post(
        "/api/v1/inventory/reservations",
        json={
            "product_id": p["id"],
            "warehouse_id": wh["id"],
            "quantity": "20",
            "ref_type": "order",
            "ref_id": order_id,
        },
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    res = r.json()
    assert res["status"] == "active"

    # available should be 30 now
    stock = client.get("/api/v1/inventory/stock", headers=_h(tok)).json()
    assert float(stock[0]["available"]) == 30.0

    # consume the reservation
    r2 = client.post(
        f"/api/v1/inventory/reservations/{res['id']}/release?consume=true",
        headers=_h(tok),
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "consumed"

    stock2 = client.get("/api/v1/inventory/stock", headers=_h(tok)).json()
    assert float(stock2[0]["quantity"]) == 30.0
    assert float(stock2[0]["reserved_quantity"]) == 0.0


def test_insufficient_stock_reservation(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()
    r = client.post(
        "/api/v1/inventory/reservations",
        json={
            "product_id": p["id"],
            "warehouse_id": wh["id"],
            "quantity": "5",
            "ref_type": "order",
            "ref_id": str(uuid.uuid4()),
        },
        headers=_h(tok),
    )
    assert r.status_code == 409


def test_low_stock_alert_triggers(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()
    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "5"},
        headers=_h(tok),
    )
    client.post(
        "/api/v1/inventory/alerts",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "threshold": "10"},
        headers=_h(tok),
    )
    # trigger: adjust below threshold
    client.post(
        "/api/v1/inventory/stock/adjust",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "-1"},
        headers=_h(tok),
    )
    r = client.get("/api/v1/inventory/alerts?only_triggered=true", headers=_h(tok))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["triggered_at"] is not None


def test_movement_history(client):
    tok = _register(client)
    wh = _setup_wh(client, tok)
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()
    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "10"},
        headers=_h(tok),
    )
    r = client.get("/api/v1/inventory/movements", headers=_h(tok))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["type"] == "receipt"