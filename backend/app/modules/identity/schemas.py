import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Organization ----------
class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- User ----------
class RegisterRequest(BaseModel):
    organization: OrganizationCreate
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class UserOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    is_active: bool
    mfa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithRolesOut(UserOut):
    roles: list[str] = []


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_slug: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------- Invitations ----------
class InviteRequest(BaseModel):
    email: EmailStr
    role_name: str = Field(min_length=2, max_length=50)


class InvitationOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role_id: uuid.UUID
    expires_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)