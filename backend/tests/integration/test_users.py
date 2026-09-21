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


def _invite_and_get_token(client, tok, email, role_name):
    from app.core.db import SessionLocal
    from app.core.uow import UnitOfWork
    from app.modules.identity import service as id_service
    from app.modules.identity.schemas import InviteRequest

    me = client.get("/api/v1/auth/me", headers=_h(tok)).json()
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        _inv, token = id_service.invite_user(
            uow,
            uuid.UUID(me["organization_id"]),
            uuid.UUID(me["id"]),
            InviteRequest(email=email, role_name=role_name),
        )
    finally:
        session.close()
    return token


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
    token = _invite_and_get_token(client, tok, "driver@test.com", "driver")

    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "password123", "full_name": "Driver"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "driver@test.com"


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
    token = _invite_and_get_token(client, tok, "staff@test.com", "warehouse_staff")

    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "password123", "full_name": "Staff"},
    )
    new_user_id = r.json()["id"]

    r2 = client.post(f"/api/v1/users/{new_user_id}/deactivate", headers=_h(tok))
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
    # no driver linked yet → 404
    r = client.get("/api/v1/drivers/me", headers=_h(tok))
    assert r.status_code == 404