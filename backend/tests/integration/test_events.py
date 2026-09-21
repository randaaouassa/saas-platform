import uuid


def _register(client, slug=None):
    slug = slug or f"ev-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Ev Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_order_creation_emits_event(client, db):
    from sqlalchemy import select

    from app.core.events.models import DomainEvent

    tok = _register(client)
    wh = client.post(
        "/api/v1/warehouses", json={"name": "WH", "code": "WH1"}, headers=_h(tok)
    ).json()
    p = client.post(
        "/api/v1/inventory/products",
        json={"sku": "SKU1", "name": "Widget"},
        headers=_h(tok),
    ).json()
    c = client.post("/api/v1/customers", json={"name": "Jane"}, headers=_h(tok)).json()
    client.post(
        "/api/v1/orders",
        json={
            "customer_id": c["id"],
            "number": "O-1",
            "warehouse_id": wh["id"],
            "items": [{"product_id": p["id"], "quantity": "1", "unit_price": "1"}],
        },
        headers=_h(tok),
    )
    db.expire_all()
    events = list(db.scalars(select(DomainEvent).where(DomainEvent.type == "order.created")))
    assert len(events) == 1
    assert events[0].aggregate_type == "order"


def test_delivery_transition_emits_event(client, db):
    from sqlalchemy import select

    from app.core.events.models import DomainEvent

    tok = _register(client)
    d = client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    ).json()
    client.post(
        f"/api/v1/deliveries/{d['id']}/status",
        json={"status": "assigned"},
        headers=_h(tok),
    )
    db.expire_all()
    events = list(
        db.scalars(select(DomainEvent).where(DomainEvent.type == "delivery.assigned"))
    )
    assert len(events) == 1


def test_dispatcher_marks_published(client, db):
    from sqlalchemy import select

    from app.core.events.dispatcher import dispatch_once
    from app.core.events.models import DomainEvent

    tok = _register(client)
    client.post(
        "/api/v1/deliveries",
        json={"dropoff_location": "X"},
        headers=_h(tok),
    )

    n = dispatch_once(session=db)
    assert n >= 1

    db.expire_all()
    events = list(
        db.scalars(select(DomainEvent).where(DomainEvent.published_at.is_not(None)))
    )
    assert len(events) >= 1