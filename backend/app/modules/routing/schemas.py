import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Stop ----------
class StopOut(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    delivery_id: uuid.UUID
    sequence: int
    eta: datetime | None
    arrived_at: datetime | None
    departed_at: datetime | None
    status: str

    model_config = {"from_attributes": True}


class StopStatusUpdate(BaseModel):
    status: str = Field(max_length=20)


# ---------- Route ----------
class RouteCreate(BaseModel):
    driver_id: uuid.UUID
    date: date
    delivery_ids: list[uuid.UUID] = Field(min_length=1)


class RouteOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    driver_id: uuid.UUID
    date: date
    status: str
    total_distance_m: Decimal | None
    total_duration_s: Decimal | None
    created_at: datetime
    updated_at: datetime
    stops: list[StopOut] = []

    model_config = {"from_attributes": True}


class RouteRecalcRequest(BaseModel):
    reason: str = Field(max_length=255)


class RouteRecalculationOut(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    reason: str
    before_json: dict
    after_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}