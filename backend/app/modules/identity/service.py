import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import AuthError, ConflictError, NotFoundError
from app.core.events.publisher import emit
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
    PasswordResetToken,
    Permission,
    Role,
    User,
    UserRole,
)
from app.modules.identity.models import (
    Session as SessionModel,
)
from app.modules.identity.schemas import (
    AcceptInviteRequest,
    InviteRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserUpdate,
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


# ---------- Registration ----------
def register_organization(
    uow: UnitOfWork, payload: RegisterRequest
) -> tuple[User, Organization]:
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
    record(db, organization_id=org.id, actor_id=user.id,
           action="org.registered", resource="organization", resource_id=str(org.id))
    emit(db, type="org.created", aggregate_type="organization", aggregate_id=org.id,
         organization_id=org.id, actor_id=user.id, payload={"slug": org.slug})
    uow.commit()
    db.refresh(user)
    db.refresh(org)
    return user, org


# ---------- Auth ----------
def authenticate(uow: UnitOfWork, payload: LoginRequest) -> User:
    db = uow.session
    org = db.scalar(select(Organization).where(Organization.slug == payload.organization_slug))
    if not org or org.status != "active":
        raise AuthError("invalid credentials")

    user = db.scalar(
        select(User).where(
            User.organization_id == org.id, User.email == payload.email.lower()
        )
    )
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise AuthError("invalid credentials")

    user.last_login_at = _now()
    record(db, organization_id=user.organization_id, actor_id=user.id,
           action="auth.login", resource="user", resource_id=str(user.id))
    uow.commit()
    db.refresh(user)
    return user


def _role_names(user: User) -> list[str]:
    return [r.name for r in user.roles]


def issue_tokens(
    uow: UnitOfWork, user: User, user_agent: str | None = None, ip: str | None = None
) -> dict:
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
    record(db, organization_id=user.organization_id, actor_id=user.id,
           action="auth.refresh", resource="session", resource_id=str(session.id))
    uow.commit()
    return issue_tokens(uow, user)


def logout(uow: UnitOfWork, refresh_token: str) -> None:
    db = uow.session
    token_hash = _hash_token(refresh_token)
    session = db.scalar(select(SessionModel).where(SessionModel.refresh_token_hash == token_hash))
    if session and session.revoked_at is None:
        session.revoked_at = _now()
        record(db, organization_id=None, actor_id=session.user_id,
               action="auth.logout", resource="session", resource_id=str(session.id))
        uow.commit()


# ---------- Invitations ----------
def invite_user(
    uow: UnitOfWork, org_id: uuid.UUID, invited_by: uuid.UUID, payload: InviteRequest
) -> tuple[Invitation, str]:
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
    record(db, organization_id=org_id, actor_id=invited_by,
           action="user.invited", resource="invitation", resource_id=str(inv.id),
           metadata={"email": inv.email, "role_id": str(inv.role_id)})
    emit(db, type="user.invited", aggregate_type="invitation", aggregate_id=inv.id,
         organization_id=org_id, actor_id=invited_by,
         payload={"email": inv.email, "role": payload.role_name})
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
    record(db, organization_id=inv.organization_id, actor_id=user.id,
           action="user.joined", resource="user", resource_id=str(user.id))
    emit(db, type="user.joined", aggregate_type="user", aggregate_id=user.id,
         organization_id=inv.organization_id, actor_id=user.id, payload={"email": user.email})
    uow.commit()
    db.refresh(user)
    return user


# ---------- Users ----------
def list_users(uow: UnitOfWork, org_id: uuid.UUID) -> list[User]:
    return list(
        uow.session.scalars(
            select(User).where(User.organization_id == org_id).order_by(User.created_at)
        )
    )


def get_user(uow: UnitOfWork, org_id: uuid.UUID, user_id: uuid.UUID) -> User:
    u = uow.session.scalar(
        select(User).where(User.id == user_id, User.organization_id == org_id)
    )
    if not u:
        raise NotFoundError("user not found")
    return u


def update_user(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, user_id: uuid.UUID, payload: UserUpdate
) -> User:
    u = get_user(uow, org_id, user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="user.updated", resource="user", resource_id=str(u.id))
    uow.commit()
    uow.session.refresh(u)
    return u


def deactivate_user(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, user_id: uuid.UUID
) -> User:
    u = get_user(uow, org_id, user_id)
    u.is_active = False
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="user.deactivated", resource="user", resource_id=str(u.id))
    uow.commit()
    uow.session.refresh(u)
    return u


# ---------- Roles ----------
def list_roles(uow: UnitOfWork, org_id: uuid.UUID) -> list[Role]:
    return list(
        uow.session.scalars(
            select(Role).where(Role.organization_id == org_id).order_by(Role.name)
        )
    )


def list_permissions(uow: UnitOfWork) -> list[Permission]:
    return list(uow.session.scalars(select(Permission).order_by(Permission.code)))


def assign_role(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, user_id: uuid.UUID, role_name: str
) -> User:
    db = uow.session
    user = get_user(uow, org_id, user_id)
    role = db.scalar(
        select(Role).where(Role.organization_id == org_id, Role.name == role_name)
    )
    if not role:
        raise NotFoundError("role not found")

    exists = db.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if exists:
        raise ConflictError("user already has this role")

    db.add(UserRole(user_id=user.id, role_id=role.id))
    record(db, organization_id=org_id, actor_id=actor_id,
           action="user.role_assigned", resource="user", resource_id=str(user.id),
           metadata={"role": role_name})
    uow.commit()
    db.refresh(user)
    return user


def revoke_role(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, user_id: uuid.UUID, role_name: str
) -> User:
    db = uow.session
    user = get_user(uow, org_id, user_id)
    role = db.scalar(
        select(Role).where(Role.organization_id == org_id, Role.name == role_name)
    )
    if not role:
        raise NotFoundError("role not found")

    link = db.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if not link:
        raise NotFoundError("user does not have this role")

    db.delete(link)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="user.role_revoked", resource="user", resource_id=str(user.id),
           metadata={"role": role_name})
    uow.commit()
    db.refresh(user)
    return user


# ---------- Password reset ----------
def forgot_password(
    uow: UnitOfWork, email: str, organization_slug: str
) -> tuple[User | None, str | None]:
    """Returns (user, token) if user exists; else (None, None) to avoid user enumeration."""
    db = uow.session
    org = db.scalar(select(Organization).where(Organization.slug == organization_slug))
    if not org:
        return None, None
    user = db.scalar(
        select(User).where(User.organization_id == org.id, User.email == email.lower())
    )
    if not user or not user.is_active:
        return None, None

    token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=_now() + timedelta(hours=1),
        )
    )
    emit(db, type="user.password_reset_requested", aggregate_type="user", aggregate_id=user.id,
         organization_id=org.id, actor_id=user.id, payload={"email": user.email})
    uow.commit()
    return user, token


def reset_password(uow: UnitOfWork, payload: ResetPasswordRequest) -> User:
    db = uow.session
    token_hash = _hash_token(payload.token)
    row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    if not row or row.used_at is not None or row.expires_at < _now():
        raise AuthError("invalid or expired reset token")

    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise AuthError("user inactive")

    user.hashed_password = hash_password(payload.new_password)
    row.used_at = _now()

    # revoke all sessions on password change
    db.query(SessionModel).filter(SessionModel.user_id == user.id).update(
        {"revoked_at": _now()}
    )
    record(db, organization_id=user.organization_id, actor_id=user.id,
           action="user.password_reset", resource="user", resource_id=str(user.id))
    uow.commit()
    db.refresh(user)
    return user


def get_user_or_404(uow: UnitOfWork, user_id: uuid.UUID) -> User:
    user = uow.session.get(User, user_id)
    if not user:
        raise NotFoundError("user not found")
    return user