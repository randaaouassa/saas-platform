import uuid

import pytest
from pydantic import ValidationError

from app.shared.pagination import (
    PageParams,
    decode_cursor,
    encode_cursor,
)


def test_encode_decode_roundtrip():
    uid = uuid.uuid4()
    cur = encode_cursor(uid)
    assert decode_cursor(cur) == uid


def test_decode_invalid_returns_none():
    assert decode_cursor("not-a-cursor") is None
    assert decode_cursor(None) is None


def test_page_params_validation():
    p = PageParams(limit=50)
    assert p.limit == 50
    with pytest.raises(ValidationError):
        PageParams(limit=0)
    with pytest.raises(ValidationError):
        PageParams(limit=1000)