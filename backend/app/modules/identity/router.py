from fastapi import APIRouter, Depends, Request, status

from app.core.uow import UnitOfWork, get_uow
from app.modules.identity import service
from app.modules.identity.deps import get_current_user, require_roles
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    AcceptInviteRequest,
    InvitationOut,
    InviteRequest,
    LoginRequest,
    OrganizationOut,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, uow: UnitOfWork = Depends(get_uow)) -> TokenPair:
    user, _org = service.register_organization(uow, payload)
    tokens = service.issue_tokens(
        uow, user, user_agent=request.headers.get("user-agent"), ip=request.client.host if request.client else None
    )
    return TokenPair(**tokens)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, uow: UnitOfWork = Depends(get_uow)) -> TokenPair:
    user = service.authenticate(uow, payload)
    tokens = service.issue_tokens(
        uow, user, user_agent=request.headers.get("user-agent"), ip=request.client.host if request.client else None
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


@router.post("/invitations", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def invite(
    payload: InviteRequest,
    user: User = Depends(require_roles("org_admin")),
    uow: UnitOfWork = Depends(get_uow),
) -> InvitationOut:
    inv, _token = service.invite_user(uow, user.organization_id, user.id, payload)
    return InvitationOut.model_validate(inv)


@router.post("/invitations/accept", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def accept_invite(payload: AcceptInviteRequest, uow: UnitOfWork = Depends(get_uow)) -> UserOut:
    user = service.accept_invite(uow, payload)
    return UserOut.model_validate(user)