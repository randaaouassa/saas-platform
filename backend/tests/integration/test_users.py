import uuid


def _register(client, slug=None):
    slug = slug or f"usr-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization": {"name": "Usr Org", "slug": slug},
            "email": f"admin@{slug}.com",
            "password": "password123",
            "full_name": "Admin",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"], slug


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _invite_token(client, tok, email, role_name):
    r = client.post(
        "/api/v1/auth/invitations",
        json={"email": email, "role_name": role_name},
        headers=_h(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["token"]


def test_list_users_and_roles(client):
    tok, _ = _register(client)
    r = client.get("/api/v1/users", headers=_h(tok))
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
    assert "org_admin" in r.json()[0]["roles"]

    r2 = client.get("/api/v1/roles", headers=_h(tok))
    assert r2.status_code == 200
    names = {x["name"] for x in r2.json()}
    assert "org_admin" in names and "driver" in names


def test_accept_invite(client):
    tok, _ = _register(client)
    token = _invite_token(client, tok, "driver@test.com", "driver")

    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "password123", "full_name": "Driver"},
    )
    assert r.status_code == 201, r.text
    assert "access_token" in r.json()


def test_forgot_and_reset_password(client):
    tok, slug = _register(client)
    me = client.get("/api/v1/auth/me", headers=_h(tok)).json()

    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": me["email"], "organization_slug": slug},
    )
    assert r.status_code == 200
    token = r.json().get("token")
    assert token

    r2 = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r2.status_code == 200

    r3 = client.post(
        "/api/v1/auth/login",
        json={"email": me["email"], "password": "newpassword123", "organization_slug": slug},
    )
    assert r3.status_code == 200


def test_deactivate_user(client):
    tok, _ = _register(client)
    token = _invite_token(client, tok, "staff@test.com", "warehouse_staff")

    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "password123", "full_name": "Staff"},
    )
    assert r.status_code == 201, r.text

    users = client.get("/api/v1/users", headers=_h(tok)).json()
    new_user = [u for u in users if u["email"] == "staff@test.com"][0]

    r2 = client.post(f"/api/v1/users/{new_user['id']}/deactivate", headers=_h(tok))
    assert r2.status_code == 200
    assert r2.json()["is_active"] is False


def test_assign_and_revoke_role(client):
    tok, _ = _register(client)
    me = client.get("/api/v1/auth/me", headers=_h(tok)).json()

    r = client.post(
        f"/api/v1/users/{me['id']}/roles",
        json={"role_name": "dispatcher"},
        headers=_h(tok),
    )
    assert r.status_code == 200, r.text
    assert "dispatcher" in r.json()["roles"]

    r2 = client.delete(f"/api/v1/users/{me['id']}/roles/dispatcher", headers=_h(tok))
    assert r2.status_code == 200
    assert "dispatcher" not in r2.json()["roles"]


def test_driver_me_endpoint(client):
    tok, _ = _register(client)
    r = client.get("/api/v1/drivers/me", headers=_h(tok))
    assert r.status_code == 404