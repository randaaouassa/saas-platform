import base64
import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    cursor: str | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False


def encode_cursor(id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(str(id).encode()).decode()


def decode_cursor(cursor: str | None) -> uuid.UUID | None:
    if not cursor:
        return None
    try:
        return uuid.UUID(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return None


def paginate_by_id(
    db: Session,
    query: Select,
    params: PageParams,
    *,
    model,
) -> tuple[list, str | None, bool]:
    """Keyset pagination by id descending. Requires UUID PK."""
    after_id = decode_cursor(params.cursor)
    q = query.order_by(model.id.desc()).limit(params.limit + 1)
    if after_id is not None:
        q = q.where(model.id < after_id)
    rows = list(db.scalars(q))
    has_more = len(rows) > params.limit
    rows = rows[: params.limit]
    next_cursor = encode_cursor(rows[-1].id) if has_more and rows else None
    return rows, next_cursor, has_more