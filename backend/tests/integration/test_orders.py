import uuid


def _register(client, slug=None):
    slug = slug or f"ord-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Ord Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _setup_full(client, tok, qty="100"):
    u = uuid.uuid4().hex[:6]
    wh = client.post(
        "/api/v1/warehouses",
        json={"name": "WH", "code": f"WH{u}"},
        headers=_h(tok),
    ).json()
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": f"SKU-{u}", "name": "Widget"},
        headers=_h(tok),
    ).json()
    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": qty},
        headers=_h(tok),
    )
    c = client.post(
        "/api/v1/customers",
        json={"name": "Jane", "address": "1 Main St", "lat": 1.0, "lng": 2.0},
        headers=_h(tok),
    ).json()
    return wh, p, c


def test_create_customer_and_order(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]

    r = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "currency": "USD",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "5", "unit_price": "10.00"}],
        },
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    o = r.json()
    assert o["status"] == "draft"
    assert float(o["total_amount"]) == 50.0
    assert len(o["items"]) == 1


def test_duplicate_order_number(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]
    payload = {
        "customer_id": c["id"],
        "number": f"ORD-{u}",
        "warehouse_id": wh["id"],
        "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
    }
    assert client.post("/api/v1/orders", json=payload, headers=_h(tok)).status_code == 201
    assert client.post("/api/v1/orders", json=payload, headers=_h(tok)).status_code == 409


def test_order_lifecycle_reserves_and_consumes_stock(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok, qty="20")
    u = uuid.uuid4().hex[:6]

    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "5", "unit_price": "10"}],
        },
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/orders/{o['id']}/status",
        json={"status": "confirmed"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed"

    r2 = client.post(
        f"/api/v1/orders/{o['id']}/status?warehouse_id={wh['id']}",
        json={"status": "reserved"},
        headers=_h(tok),
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "reserved"

    stock = client.get("/api/v1/inventory/stock", headers=_h(tok)).json()
    assert float(stock[0]["reserved_quantity"]) == 5.0

    for s in ["picking", "packed", "ready_for_dispatch", "dispatched"]:
        r = client.post(
            f"/api/v1/orders/{o['id']}/status",
            json={"status": s},
            headers=_h(tok),
        )
        assert r.status_code == 200, (s, r.text)

    stock2 = client.get("/api/v1/inventory/stock", headers=_h(tok)).json()
    assert float(stock2[0]["quantity"]) == 15.0
    assert float(stock2[0]["reserved_quantity"]) == 0.0


def test_invalid_transition(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]
    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
        },
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/orders/{o['id']}/status",
        json={"status": "delivered"},
        headers=_h(tok),
    )
    assert r.status_code == 422


def test_cancellation_releases_reservations(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok, qty="10")
    u = uuid.uuid4().hex[:6]
    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "3", "unit_price": "1"}],
        },
        headers=_h(tok),
    ).json()

    client.post(f"/api/v1/orders/{o['id']}/status", json={"status": "confirmed"}, headers=_h(tok))
    client.post(
        f"/api/v1/orders/{o['id']}/status?warehouse_id={wh['id']}",
        json={"status": "reserved"},
        headers=_h(tok),
    )
    r = client.post(
        f"/api/v1/orders/{o['id']}/status",
        json={"status": "cancelled", "reason": "customer request"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    stock = client.get("/api/v1/inventory/stock", headers=_h(tok)).json()
    assert float(stock[0]["reserved_quantity"]) == 0.0


def test_order_history(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]
    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
        },
        headers=_h(tok),
    ).json()
    client.post(f"/api/v1/orders/{o['id']}/status", json={"status": "confirmed"}, headers=_h(tok))

    r = client.get(f"/api/v1/orders/{o['id']}/history", headers=_h(tok))
    assert r.status_code == 200
    hist = r.json()
    assert len(hist) == 2
    assert hist[0]["to_status"] == "draft"
    assert hist[1]["to_status"] == "confirmed"


def test_tenant_isolation_orders(client):
    tok1 = _register(client)
    tok2 = _register(client)
    wh, p, c = _setup_full(client, tok1)
    u = uuid.uuid4().hex[:6]
    client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
        },
        headers=_h(tok1),
    )
    r = client.get("/api/v1/orders", headers=_h(tok2))
    assert r.status_code == 200
    assert r.json() == []


def test_update_add_remove_item(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]
    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "10"}],
        },
        headers=_h(tok),
    ).json()

    r = client.patch(
        f"/api/v1/orders/{o['id']}",
        json={"notes": "urgent"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["notes"] == "urgent"

    r2 = client.post(
        f"/api/v1/orders/{o['id']}/items",
        json={"product_id": p["id"], "quantity": "2", "unit_price": "10"},
        headers=_h(tok),
    )
    assert r2.status_code == 200
    assert float(r2.json()["total_amount"]) == 30.0
    assert len(r2.json()["items"]) == 2

    item_id = r2.json()["items"][-1]["id"]
    r3 = client.delete(f"/api/v1/orders/{o['id']}/items/{item_id}", headers=_h(tok))
    assert r3.status_code == 200
    assert float(r3.json()["total_amount"]) == 10.0


def test_cancel_order_direct(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]
    o = client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"ORD-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
        },
        headers=_h(tok),
    ).json()

    r = client.post(
        f"/api/v1/orders/{o['id']}/cancel",
        json={"reason": "changed mind"},
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    r2 = client.post(
        f"/api/v1/orders/{o['id']}/cancel",
        json={"reason": "again"},
        headers=_h(tok),
    )
    assert r2.status_code == 409


def test_import_orders(client):
    tok = _register(client)
    wh, p, c = _setup_full(client, tok)
    u = uuid.uuid4().hex[:6]

    r = client.post(
        "/api/v1/orders/import",
        json={
            "warehouse_id": wh["id"],
            "rows": [
                {
                    "number": f"IMP-{u}-1",
                    "customer_name": "Import Customer",
                    "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "5"}],
                },
                {
                    "number": f"IMP-{u}-2",
                    "customer_name": "Import Customer",
                    "items": [{"product_id": p["id"], "quantity": "2", "unit_price": "5"}],
                },
            ],
        },
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 2
    assert r.json()["errors"] == []