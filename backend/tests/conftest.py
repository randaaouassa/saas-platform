import os
import uuid

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@db:5432/saas_platform_test",
)

ADMIN_DB_URL = "postgresql+psycopg://postgres:postgres@db:5432/postgres"


@pytest.fixture(scope="session", autouse=True)
def _create_test_db():
    admin = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'saas_platform_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE saas_platform_test"))
    admin.dispose()
    yield


@pytest.fixture(scope="session")
def engine(_create_test_db):
    eng = create_engine(TEST_DB_URL, future=True)
    import app.core.audit
    import app.modules  # noqa: F401
    from app.core.db import Base
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session: Session = SessionLocal()
    from app.core.db import Base
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    from app.core.uow import UnitOfWork, get_uow
    from app.main import app

    def _get_uow_override():
        yield UnitOfWork(db)

    app.dependency_overrides[get_uow] = _get_uow_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def org_payload():
    slug = f"test-{uuid.uuid4().hex[:8]}"
    return {
        "organization": {"name": "Test Org", "slug": slug},
        "email": f"admin@{slug}.com",
        "password": "password123",
        "full_name": "Test Admin",
    }