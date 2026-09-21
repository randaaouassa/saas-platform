import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Package ----------
class PackageCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    volume: Decimal | None = None


class PackageOut(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    code: str
    weight: Decimal | None
    length: Decimal | None
    width: Decimal | None
    height: Decimal | None
    volume: Decimal | None

    model_config = {"from_attributes": True}


# ---------- Delivery ----------
class DeliveryCreate(BaseModel):
    order_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    pickup_location: str = Field(default="", max_length=500)
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    dropoff_location: str = Field(min_length=1, max_length=500)
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    scheduled_at: datetime | None = None
    packages: list[PackageCreate] = []


class DeliveryOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    order_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    pickup_location: str
    pickup_lat: float | None
    pickup_lng: float | None
    dropoff_location: str
    dropoff_lat: float | None
    dropoff_lng: float | None
    status: str
    scheduled_at: datetime | None
    delivered_at: datetime | None
    failed_reason: str | None
    created_at: datetime
    updated_at: datetime
    packages: list[PackageOut] = []

    model_config = {"from_attributes": True}


class DeliveryStatusUpdate(BaseModel):
    status: str = Field(max_length=30)
    lat: float | None = None
    lng: float | None = None
    note: str | None = Field(default=None, max_length=500)
    failed_reason: str | None = Field(default=None, max_length=500)


class DeliveryStatusHistoryOut(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_id: uuid.UUID | None
    lat: float | None
    lng: float | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- POD ----------
class PODCreate(BaseModel):
    kind: str = Field(max_length=30)
    s3_key: str | None = Field(default=None, max_length=500)
    signer_name: str | None = Field(default=None, max_length=255)
    signature_s3_key: str | None = Field(default=None, max_length=500)
    lat: float | None = None
    lng: float | None = None


class PODOut(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    kind: str
    s3_key: str | None
    signer_name: str | None
    signature_s3_key: str | None
    lat: float | None
    lng: float | None
    captured_at: datetime

    model_config = {"from_attributes": True}