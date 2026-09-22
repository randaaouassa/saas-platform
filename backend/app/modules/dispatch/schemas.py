import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CandidateOut(BaseModel):
    driver_id: uuid.UUID
    full_name: str
    status: str
    vehicle_id: uuid.UUID | None
    distance_km: float | None
    active_deliveries: int
    package_weight: float
    vehicle_capacity: float | None
    capacity_ok: bool
    score: float
    factors: dict


class RankCandidatesRequest(BaseModel):
    delivery_id: uuid.UUID


class RankCandidatesResponse(BaseModel):
    delivery_id: uuid.UUID
    candidates: list[CandidateOut]


class AssignRequest(BaseModel):
    delivery_id: uuid.UUID
    driver_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None


class ReassignRequest(BaseModel):
    delivery_id: uuid.UUID
    new_driver_id: uuid.UUID
    new_vehicle_id: uuid.UUID | None = None
    reason: str = Field(default="", max_length=255)


class UnassignRequest(BaseModel):
    delivery_id: uuid.UUID
    reason: str = Field(default="", max_length=255)


class AssignmentOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    delivery_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID | None
    score: Decimal
    mode: str
    status: str
    assigned_by: uuid.UUID | None
    assigned_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentStatusUpdate(BaseModel):
    status: str = Field(max_length=20)