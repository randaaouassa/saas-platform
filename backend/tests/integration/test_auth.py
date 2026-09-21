def test_register_creates_org_and_user(client, org_payload):
    r = client.post("/api/v1/auth/register", json=org_payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_register_duplicate_slug(client, org_payload):
    client.post("/api/v1/auth/register", json=org_payload)
    r = client.post("/api/v1/auth/register", json=org_payload)
    assert r.status_code == 409


def test_login_success(client, org_payload):
    client.post("/api/v1/auth/register", json=org_payload)
    r = client.post(
        "/api/v1/auth/login",
        json={
            "email": org_payload["email"],
            "password": org_payload["password"],
            "organization_slug": org_payload["organization"]["slug"],
        },
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client, org_payload):
    client.post("/api/v1/auth/register", json=org_payload)
    r = client.post(
        "/api/v1/auth/login",
        json={
            "email": org_payload["email"],
            "password": "wrong",
            "organization_slug": org_payload["organization"]["slug"],
        },
    )
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_returns_user(client, org_payload):
    reg = client.post("/api/v1/auth/register", json=org_payload).json()
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == org_payload["email"]


def test_refresh_rotates(client, org_payload):
    reg = client.post("/api/v1/auth/register", json=org_payload).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != reg["refresh_token"]
    # old refresh reused -> 401
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": reg["refresh_token"]})
    assert r2.status_code == 401
    

def test_logout_revokes(client, org_payload):
    reg = client.post("/api/v1/auth/register", json=org_payload).json()
    r = client.post("/api/v1/auth/logout", json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 204
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": reg["refresh_token"]})
    assert r2.status_code == 401


def test_invite_requires_admin_role(client, org_payload):
    reg = client.post("/api/v1/auth/register", json=org_payload).json()
    r = client.post(
        "/api/v1/auth/invitations",
        json={"email": "staff@test.com", "role_name": "warehouse_staff"},
        headers={"Authorization": f"Bearer {reg['access_token']}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "staff@test.com"