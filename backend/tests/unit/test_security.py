from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    h = hash_password("s3cret-pw")
    assert h != "s3cret-pw"
    assert verify_password("s3cret-pw", h)
    assert not verify_password("wrong", h)


def test_access_token_roundtrip():
    tok = create_access_token("user-1", extra={"org": "o1", "roles": ["org_admin"]})
    payload = decode_token(tok)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"
    assert payload["org"] == "o1"
    assert payload["roles"] == ["org_admin"]


def test_refresh_token_roundtrip():
    tok = create_refresh_token("user-2")
    payload = decode_token(tok)
    assert payload["sub"] == "user-2"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    import pytest
    with pytest.raises(ValueError):
        decode_token("not-a-token")