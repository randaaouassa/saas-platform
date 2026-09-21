from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.db import SessionLocal


class UnitOfWork:
    """Groups DB work into one transaction. Commit or rollback as a whole."""

    def __init__(self, session: Session):
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def flush(self) -> None:
        self.session.flush()


def get_uow() -> Generator[UnitOfWork, None, None]:
    session = SessionLocal()
    uow = UnitOfWork(session)
    try:
        yield uow
    except Exception:
        uow.rollback()
        raise
    finally:
        session.close()