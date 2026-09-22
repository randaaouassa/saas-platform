import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    name: str
    version: str
    env: str


class OrgSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    status: str
    users_count: int
    created_at: datetime


class SystemStats(BaseModel):
    organizations: int
    users: int
    warehouses: int
    products: int
    orders: int
    deliveries: int
    drivers: int
    active_orgs: int
    suspended_orgs: int


class OrgStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(active|suspended)$")