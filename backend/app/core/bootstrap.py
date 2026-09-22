import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.modules.identity.models import Organization, Role, User, UserRole

log = structlog.get_logger("bootstrap")


def ensure_super_admin() -> None:
    if not settings.SUPER_ADMIN_EMAIL or not settings.SUPER_ADMIN_PASSWORD:
        return

    session = SessionLocal()
    try:
        org = session.scalar(select(Organization).where(Organization.slug == "platform"))
        if not org:
            org = Organization(name="Platform", slug="platform", plan="internal")
            session.add(org)
            session.flush()

        role = session.scalar(
            select(Role).where(Role.organization_id == org.id, Role.name == "super_admin")
        )
        if not role:
            role = Role(organization_id=org.id, name="super_admin", is_system=True)
            session.add(role)
            session.flush()

        user = session.scalar(
            select(User).where(
                User.organization_id == org.id,
                User.email == settings.SUPER_ADMIN_EMAIL.lower(),
            )
        )
        if not user:
            user = User(
                organization_id=org.id,
                email=settings.SUPER_ADMIN_EMAIL.lower(),
                hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                full_name="Super Admin",
            )
            session.add(user)
            session.flush()
            session.add(UserRole(user_id=user.id, role_id=role.id))
            log.info("super_admin_created", email=user.email)
        session.commit()
    finally:
        session.close()