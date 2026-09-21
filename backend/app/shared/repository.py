import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class TenantRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    def base_query(self) -> Select:
        return select(self.model).where(self.model.organization_id == self.organization_id)

    def get(self, id: uuid.UUID) -> ModelT | None:
        return self.db.scalar(self.base_query().where(self.model.id == id))

    def list(self, *, limit: int = 25, offset: int = 0, **filters: Any) -> list[ModelT]:
        q = self.base_query()
        for k, v in filters.items():
            q = q.where(getattr(self.model, k) == v)
        q = q.limit(limit).offset(offset)
        return list(self.db.scalars(q))

    def add(self, obj: ModelT) -> ModelT:
        obj.organization_id = self.organization_id  # type: ignore[attr-defined]
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)