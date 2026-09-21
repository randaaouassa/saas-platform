import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Driver ----------
class DriverCreate(BaseModel):
    user_id: uuid.UUID | None = None
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    license_no: str | None = Field(default=None, max_length=100)


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    license_no: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=30)
    rating: Decimal | None = None


class DriverOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None
    full_name: str
    phone: str | None
    license_no: str | None
    status: str
    rating: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Vehicle ----------
class VehicleCreate(BaseModel):
    driver_id: uuid.UUID | None = None
    plate: str = Field(min_length=1, max_length=20)
    type: str = Field(max_length=30)
    capacity_weight: Decimal | None = None
    capacity_volume: Decimal | None = None


class VehicleOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    driver_id: uuid.UUID | None
    plate: str
    type: str
    capacity_weight: Decimal | None
    capacity_volume: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Shift ----------
class ShiftStart(BaseModel):
    driver_id: uuid.UUID


class ShiftOut(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    status: str

    model_config = {"from_attributes": True}


# ---------- Position ----------
class PositionCreate(BaseModel):
    lat: float
    lng: float
    heading: float | None = None
    speed: float | None = None


class PositionOut(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    lat: float
    lng: float
    heading: float | None
    speed: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}