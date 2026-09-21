from fastapi import APIRouter, Depends, Request, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity import service
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    InvitationOut,
    InviteRequest,
    LoginRequest,
    OrganizationOut,
    PermissionOut,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RoleOut,
    TokenPair,
    UserOut,
    UserRoleChange,
    UserUpdate,
    UserWithRolesOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])
roles_router = APIRouter(prefix="/roles", tags=["roles"])


# ---------- Auth ----------
@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, request: Request, uow: UnitOfWork = Depends(get_uow)
) -> TokenPair:
    user, _org = service.register_organization(uow, payload)
    tokens = service.issue_tokens(
        uow, user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    return TokenPair(**tokens)


@router.post("/login", response_model=TokenPair)
def login(
    payload: LoginRequest, request: Request, uow: UnitOfWork = Depends(get_uow)
) -> TokenPair:
    user = service.authenticate(uow, payload)
    tokens = service.issue_tokens(
        uow, user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    return TokenPair(**tokens)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, uow: UnitOfWork = Depends(get_uow)) -> TokenPair:
    return TokenPair(**service.rotate_refresh(uow, payload.refresh_token))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, uow: UnitOfWork = Depends(get_uow)) -> None:
    service.logout(uow, payload.refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/me/organization", response_model=OrganizationOut)
def my_organization(user: User = Depends(get_current_user)) -> OrganizationOut:
    return OrganizationOut.model_validate(user.organization)


# ---------- Invitations ----------
@router.post(
    "/invitations", response_model=InvitationOut, status_code=status.HTTP_201_CREATED
)
def invite(
    payload: InviteRequest,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> InvitationOut:
    inv, _token = service.invite_user(uow, user.organization_id, user.id, payload)
    return InvitationOut.model_validate(inv)


@router.post(
    "/invitations/accept", response_model=UserOut, status_code=status.HTTP_201_CREATED
)
def accept_invite(
    payload: AcceptInviteRequest, uow: UnitOfWork = Depends(get_uow)
) -> UserOut:
    user = service.accept_invite(uow, payload)
    return UserOut.model_validate(user)


# ---------- Password reset ----------
@router.post("/forgot-password", response_model=dict)
def forgot_password(
    payload: ForgotPasswordRequest, uow: UnitOfWork = Depends(get_uow)
) -> dict:
    _user, token = service.forgot_password(uow, payload.email, payload.organization_slug)
    # In production: never return the token; send by email. Return token in dev only.
    from app.core.config import settings

    return {"sent": True, "token": token if settings.ENV != "prod" else None}


@router.post("/reset-password", response_model=UserOut)
def reset_password(
    payload: ResetPasswordRequest, uow: UnitOfWork = Depends(get_uow)
) -> UserOut:
    user = service.reset_password(uow, payload)
    return UserOut.model_validate(user)


# ---------- Users ----------
@users_router.get("", response_model=list[UserWithRolesOut])
def list_users(
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> list[UserWithRolesOut]:
    users = service.list_users(uow, user.organization_id)
    return [
        UserWithRolesOut(
            id=u.id,
            organization_id=u.organization_id,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            is_active=u.is_active,
            mfa_enabled=u.mfa_enabled,
            created_at=u.created_at,
            roles=[r.name for r in u.roles],
        )
        for u in users
    ]


@users_router.get("/{user_id}", response_model=UserWithRolesOut)
def get_user(
    user_id: str,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> UserWithRolesOut:
    import uuid as _uuid

    u = service.get_user(uow, user.organization_id, _uuid.UUID(user_id))
    return UserWithRolesOut(
        id=u.id,
        organization_id=u.organization_id,
        email=u.email,
        full_name=u.full_name,
        phone=u.phone,
        is_active=u.is_active,
        mfa_enabled=u.mfa_enabled,
        created_at=u.created_at,
        roles=[r.name for r in u.roles],
    )


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> UserOut:
    import uuid as _uuid

    u = service.update_user(
        uow, user.organization_id, user.id, _uuid.UUID(user_id), payload
    )
    return UserOut.model_validate(u)


@users_router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: str,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> UserOut:
    import uuid as _uuid

    u = service.deactivate_user(uow, user.organization_id, user.id, _uuid.UUID(user_id))
    return UserOut.model_validate(u)


@users_router.post("/{user_id}/roles", response_model=UserWithRolesOut)
def assign_role(
    user_id: str,
    payload: UserRoleChange,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> UserWithRolesOut:
    import uuid as _uuid

    u = service.assign_role(
        uow, user.organization_id, user.id, _uuid.UUID(user_id), payload.role_name
    )
    return UserWithRolesOut(
        id=u.id,
        organization_id=u.organization_id,
        email=u.email,
        full_name=u.full_name,
        phone=u.phone,
        is_active=u.is_active,
        mfa_enabled=u.mfa_enabled,
        created_at=u.created_at,
        roles=[r.name for r in u.roles],
    )


@users_router.delete("/{user_id}/roles/{role_name}", response_model=UserWithRolesOut)
def revoke_role(
    user_id: str,
    role_name: str,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> UserWithRolesOut:
    import uuid as _uuid

    u = service.revoke_role(
        uow, user.organization_id, user.id, _uuid.UUID(user_id), role_name
    )
    return UserWithRolesOut(
        id=u.id,
        organization_id=u.organization_id,
        email=u.email,
        full_name=u.full_name,
        phone=u.phone,
        is_active=u.is_active,
        mfa_enabled=u.mfa_enabled,
        created_at=u.created_at,
        roles=[r.name for r in u.roles],
    )


# ---------- Roles / Permissions ----------
@roles_router.get("", response_model=list[RoleOut])
def list_roles(
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> list[RoleOut]:
    return [RoleOut.model_validate(r) for r in service.list_roles(uow, user.organization_id)]


@roles_router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> list[PermissionOut]:
    return [PermissionOut.model_validate(p) for p in service.list_permissions(uow)]