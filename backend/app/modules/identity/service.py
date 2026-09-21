import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import AuthError, ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.uow import UnitOfWork
from app.modules.identity.models import (
    Invitation,
    Organization,
    Role,
    Session as SessionModel,
    User,
    UserRole,
)
from app.modules.identity.schemas import (
    AcceptInviteRequest,
    InviteRequest,
    LoginRequest,
    RegisterRequest,
)

DEFAULT_ROLES = [
    "org_admin",
    "warehouse_manager",
    "warehouse_staff",
    "dispatcher",
    "driver",
]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def register_organization(uow: UnitOfWork, payload: RegisterRequest) -> tuple[User, Organization]:
    db = uow.session
    if db.scalar(select(Organization).where(Organization.slug == payload.organization.slug)):
        raise ConflictError("organization slug already taken")

    org = Organization(name=payload.organization.name, slug=payload.organization.slug)
    db.add(org)
    uow.flush()

    roles: dict[str, Role] = {}
    for name in DEFAULT_ROLES:
        role = Role(organization_id=org.id, name=name, is_system=True)
        db.add(role)
        roles[name] = role
    uow.flush()

    user = User(
        organization_id=org.id,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    uow.flush()

    db.add(UserRole(user_id=user.id, role_id=roles["org_admin"].id))
    record(uow.session, organization_id=org.id, actor_id=user.id,
           action="org.registered", resource="organization", resource_id=str(org.id))
    uow.commit()
    db.refresh(user)
    db.refresh(org)
    return user, org


def authenticate(uow: UnitOfWork, payload: LoginRequest) -> User:
    db = uow.session
    org = db.scalar(select(Organization).where(Organization.slug == payload.organization_slug))
    if not org or org.status != "active":
        raise AuthError("invalid credentials")

    user = db.scalar(
        select(User).where(User.organization_id == org.id, User.email == payload.email.lower())
    )
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise AuthError("invalid credentials")

    user.last_login_at = _now()
    record(uow.session, organization_id=user.organization_id, actor_id=user.id,
           action="auth.login", resource="user", resource_id=str(user.id))
    uow.commit()
    db.refresh(user)
    return user


def _role_names(user: User) -> list[str]:
    return [r.name for r in user.roles]


def issue_tokens(uow: UnitOfWork, user: User, user_agent: str | None = None, ip: str | None = None) -> dict:
    access = create_access_token(
        str(user.id),
        extra={"org": str(user.organization_id), "roles": _role_names(user)},
    )
    refresh = create_refresh_token(str(user.id))

    session = SessionModel(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        expires_at=_now() + timedelta(days=7),
        user_agent=user_agent,
        ip=ip,
    )
    uow.session.add(session)
    uow.commit()

    from app.core.config import settings
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def rotate_refresh(uow: UnitOfWork, refresh_token: str) -> dict:
    db = uow.session
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise AuthError("invalid refresh token")
    if payload.get("type") != "refresh":
        raise AuthError("invalid token type")

    token_hash = _hash_token(refresh_token)
    session = db.scalar(select(SessionModel).where(SessionModel.refresh_token_hash == token_hash))
    if not session or session.revoked_at is not None or session.expires_at < _now():
        if session:
            db.query(SessionModel).filter(SessionModel.user_id == session.user_id).update(
                {"revoked_at": _now()}
            )
            uow.commit()
        raise AuthError("refresh token revoked or expired")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise AuthError("user inactive")

    session.revoked_at = _now()
    record(uow.session, organization_id=user.organization_id, actor_id=user.id,
           action="auth.refresh", resource="session", resource_id=str(session.id))
    uow.commit()
    return issue_tokens(uow, user)


def logout(uow: UnitOfWork, refresh_token: str) -> None:
    db = uow.session
    token_hash = _hash_token(refresh_token)
    session = db.scalar(select(SessionModel).where(SessionModel.refresh_token_hash == token_hash))
    if session and session.revoked_at is None:
        session.revoked_at = _now()
        record(uow.session, organization_id=None, actor_id=session.user_id,
               action="auth.logout", resource="session", resource_id=str(session.id))
        uow.commit()


def invite_user(uow: UnitOfWork, org_id: uuid.UUID, invited_by: uuid.UUID, payload: InviteRequest) -> tuple[Invitation, str]:
    db = uow.session
    role = db.scalar(
        select(Role).where(Role.organization_id == org_id, Role.name == payload.role_name)
    )
    if not role:
        raise NotFoundError("role not found")

    token = secrets.token_urlsafe(32)
    inv = Invitation(
        organization_id=org_id,
        email=payload.email.lower(),
        role_id=role.id,
        token_hash=_hash_token(token),
        expires_at=_now() + timedelta(days=7),
        invited_by=invited_by,
    )
    db.add(inv)
    uow.flush()
    record(uow.session, organization_id=org_id, actor_id=invited_by,
           action="user.invited", resource="invitation", resource_id=str(inv.id),
           metadata={"email": inv.email, "role_id": str(inv.role_id)})
    uow.commit()
    db.refresh(inv)
    return inv, token


def accept_invite(uow: UnitOfWork, payload: AcceptInviteRequest) -> User:
    db = uow.session
    token_hash = _hash_token(payload.token)
    inv = db.scalar(select(Invitation).where(Invitation.token_hash == token_hash))
    if not inv or inv.accepted_at is not None or inv.expires_at < _now():
        raise AuthError("invalid or expired invitation")

    existing = db.scalar(
        select(User).where(User.organization_id == inv.organization_id, User.email == inv.email)
    )
    if existing:
        raise ConflictError("user already exists")

    user = User(
        organization_id=inv.organization_id,
        email=inv.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    uow.flush()
    db.add(UserRole(user_id=user.id, role_id=inv.role_id))
    inv.accepted_at = _now()
    record(uow.session, organization_id=inv.organization_id, actor_id=user.id,
           action="user.joined", resource="user", resource_id=str(user.id))
    uow.commit()
    db.refresh(user)
    return user


def get_user_or_404(uow: UnitOfWork, user_id: uuid.UUID) -> User:
    user = uow.session.get(User, user_id)
    if not user:
        raise NotFoundError("user not found")
    return user