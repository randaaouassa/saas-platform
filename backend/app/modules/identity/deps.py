import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AuthError, PermissionError_
from app.core.security import decode_token
from app.core.uow import UnitOfWork, get_uow
from app.modules.identity.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    uow: UnitOfWork = Depends(get_uow),
) -> User:
    if creds is None:
        raise AuthError("missing credentials")
    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise AuthError("invalid token")
    if payload.get("type") != "access":
        raise AuthError("invalid token type")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise AuthError("invalid token subject")

    user = uow.session.get(User, user_id)
    if not user or not user.is_active:
        raise AuthError("user not found or inactive")
    return user


def get_current_org_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    return user.organization_id


def require_roles(*roles: str) -> Callable[[User], User]:
    allowed = set(roles)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if not any(r.name in allowed for r in user.roles):
            raise PermissionError_("insufficient permissions")
        return user

    return _checker