import uuid


def _register(client, slug=None):
    slug = slug or f"sys-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Sys Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _super_login(client):
    r = client.post(
        "/api/v1/auth/login",
        json={
            "email": "super@platform.io",
            "password": "changeme123",
            "organization_slug": "platform",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_version(client):
    r = client.get("/api/v1/system/version")
    assert r.status_code == 200
    assert r.json()["name"] == "saas-platform"


def test_stats_requires_super_admin(client):
    tok = _register(client)
    r = client.get("/api/v1/system/stats", headers=_h(tok))
    assert r.status_code == 403


def test_super_admin_can_read_stats(client):
    tok = _super_login(client)
    s = client.get("/api/v1/system/stats", headers=_h(tok))
    assert s.status_code == 200, s.text
    body = s.json()
    assert body["organizations"] >= 1
    assert body["users"] >= 1


def test_super_admin_list_and_suspend(client):
    _register(client)
    super_tok = _super_login(client)

    orgs = client.get("/api/v1/system/orgs", headers=_h(super_tok))
    assert orgs.status_code == 200
    target = [o for o in orgs.json() if o["slug"].startswith("sys-")][0]

    patch = client.patch(
        f"/api/v1/system/orgs/{target['id']}/status",
        json={"status": "suspended"},
        headers=_h(super_tok),
    )
    assert patch.status_code == 200, patch.text