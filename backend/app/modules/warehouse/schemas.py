import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------- Warehouse ----------
class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    address: str = Field(default="", max_length=500)
    lat: float | None = None
    lng: float | None = None
    timezone: str = Field(default="UTC", max_length=64)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    lat: float | None = None
    lng: float | None = None
    timezone: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None


class WarehouseOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    address: str
    lat: float | None
    lng: float | None
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Zone ----------
class ZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    type: str = Field(default="general", max_length=50)


class ZoneOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    warehouse_id: uuid.UUID
    name: str
    code: str
    type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Location ----------
class LocationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    kind: str = Field(default="shelf", max_length=50)
    capacity: float | None = None


class LocationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    zone_id: uuid.UUID
    code: str
    kind: str
    capacity: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Task ----------
class TaskCreate(BaseModel):
    warehouse_id: uuid.UUID
    type: str = Field(max_length=30)
    ref_type: str = Field(max_length=50)
    ref_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None


class TaskStatusUpdate(BaseModel):
    status: str = Field(max_length=30)


class TaskOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    warehouse_id: uuid.UUID
    type: str
    ref_type: str
    ref_id: uuid.UUID | None
    status: str
    assigned_to: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}