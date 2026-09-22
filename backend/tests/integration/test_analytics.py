import uuid
from datetime import date


def _register(client, slug=None):
    slug = slug or f"an-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "An Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_rebuild_and_read_overview(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]

    wh = client.post(
        "/api/v1/warehouses", json={"name": "WH", "code": f"WH{u}"}, headers=_h(tok)
    ).json()
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": f"SKU-{u}", "name": "Widget"},
        headers=_h(tok),
    ).json()
    client.post(
        "/api/v1/inventory/stock/receive",
        json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity": "10"},
        headers=_h(tok),
    )
    c = client.post(
        "/api/v1/customers", json={"name": "Jane"}, headers=_h(tok)
    ).json()
    client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"O-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "2", "unit_price": "5"}],
        },
        headers=_h(tok),
    )

    today = date.today().isoformat()
    r = client.post(f"/api/v1/analytics/rebuild?day={today}", headers=_h(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["orders_rows"] == 1
    assert body["inventory_rows"] >= 1

    ov = client.get(f"/api/v1/analytics/overview?day={today}", headers=_h(tok))
    assert ov.status_code == 200, ov.text
    data = ov.json()
    assert data["orders"]["orders_count"] == 1
    assert data["orders"]["revenue"] == 10.0
    assert len(data["inventory"]) >= 1


def test_range_summary(client):
    tok = _register(client)
    u = uuid.uuid4().hex[:6]
    today = date.today().isoformat()

    wh = client.post(
        "/api/v1/warehouses", json={"name": "WH", "code": f"WH{u}"}, headers=_h(tok)
    ).json()
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": f"SKU-{u}", "name": "Widget"},
        headers=_h(tok),
    ).json()
    c = client.post("/api/v1/customers", json={"name": "J"}, headers=_h(tok)).json()
    client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": f"O-{u}",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "3", "unit_price": "5"}],
        },
        headers=_h(tok),
    )
    client.post(f"/api/v1/analytics/rebuild?day={today}", headers=_h(tok))

    r = client.get(
        f"/api/v1/analytics/range?from={today}&to={today}", headers=_h(tok)
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_orders"] == 1
    assert body["total_revenue"] == 15.0
    assert len(body["orders"]) == 1
    assert len(body["top_products"]) >= 1


def test_avg_delivery_time(client):
    tok = _register(client)
    today = date.today().isoformat()

    d = client.post(
        "/api/v1/deliveries", json={"dropoff_location": "X"}, headers=_h(tok)
    ).json()
    for s in ["assigned", "picked_up", "in_transit", "delivered"]:
        client.post(
            f"/api/v1/deliveries/{d['id']}/status",
            json={"status": s},
            headers=_h(tok),
        )

    r = client.get(
        f"/api/v1/analytics/avg-delivery-time?from={today}&to={today}",
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sample_count"] == 1
    assert body["avg_duration_s"] is not None


def test_export_csv(client):
    tok = _register(client)
    today = date.today().isoformat()
    r = client.get(
        f"/api/v1/analytics/export/orders.csv?from={today}&to={today}",
        headers=_h(tok),
    )
    assert r.status_code == 200
    assert "date,orders_count" in r.text


def test_orders_and_deliveries_endpoints(client):
    tok = _register(client)
    today = date.today().isoformat()

    client.post(f"/api/v1/analytics/rebuild?day={today}", headers=_h(tok))

    r = client.get(f"/api/v1/analytics/orders?day={today}", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["orders_count"] == 0

    r2 = client.get(f"/api/v1/analytics/deliveries?day={today}", headers=_h(tok))
    assert r2.status_code == 200
    assert r2.json()["deliveries_count"] == 0


def test_tenant_isolation(client):
    tok1 = _register(client)
    tok2 = _register(client)
    today = date.today().isoformat()
    client.post(f"/api/v1/analytics/rebuild?day={today}", headers=_h(tok1))

    r = client.get(f"/api/v1/analytics/overview?day={today}", headers=_h(tok2))
    assert r.status_code == 200
    data = r.json()
    assert data["orders"] is None
    assert data["drivers"] == []
    assert data["inventory"] == []