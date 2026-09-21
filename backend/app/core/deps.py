from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.uow import UnitOfWork, get_uow


def db_session(session: Session = Depends(get_db)) -> Session:
    """Explicit session dependency. Prefer UoW for write endpoints."""
    return session


def uow(u: UnitOfWork = Depends(get_uow)) -> Generator[UnitOfWork, None, None]:
    yield u