from datetime import datetime

from fastapi import Query
from pydantic import BaseModel


class ListQuery(BaseModel):
    limit: int = Query(default=25, ge=1, le=100)
    cursor: str | None = Query(default=None)
    sort: str | None = Query(default=None, description="-created_at or created_at")
    q: str | None = Query(default=None, description="free text search")
    created_from: datetime | None = Query(default=None)
    created_to: datetime | None = Query(default=None)


def apply_time_range(query, model, created_from: datetime | None, created_to: datetime | None):
    if created_from is not None:
        query = query.where(model.created_at >= created_from)
    if created_to is not None:
        query = query.where(model.created_at <= created_to)
    return query


def apply_search(query, model, term: str | None, fields: list[str]):
    if not term:
        return query
    like = f"%{term.lower()}%"
    clauses = [getattr(model, f).ilike(like) for f in fields if hasattr(model, f)]
    if not clauses:
        return query
    from sqlalchemy import or_
    return query.where(or_(*clauses))


def parse_sort(sort: str | None, default: str = "-created_at") -> tuple[str, str]:
    s = (sort or default).strip()
    desc = s.startswith("-")
    field = s[1:] if desc else s
    return field, "desc" if desc else "asc"


def apply_sort(query, model, sort: str | None, allowed: set[str]):
    field, direction = parse_sort(sort)
    if field not in allowed or not hasattr(model, field):
        field = "created_at"
    col = getattr(model, field)
    return query.order_by(col.desc() if direction == "desc" else col.asc())