import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Product ----------
class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    unit: str = Field(default="pc", max_length=20)
    barcode: str | None = Field(default=None, max_length=100)
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=20)
    barcode: str | None = Field(default=None, max_length=100)
    weight: Decimal | None = None
    length: Decimal | None = None
    width: Decimal | None = None
    height: Decimal | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    sku: str
    name: str
    description: str
    unit: str
    barcode: str | None
    weight: Decimal | None
    length: Decimal | None
    width: Decimal | None
    height: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Stock ----------
class StockReceive(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    location_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)


class StockAdjust(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    location_id: uuid.UUID | None = None
    quantity: Decimal  # signed; positive add, negative subtract
    reason: str = Field(default="", max_length=255)


class StockOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    location_id: uuid.UUID | None
    quantity: Decimal
    reserved_quantity: Decimal
    available: Decimal

    model_config = {"from_attributes": True}


# ---------- Reservation ----------
class ReservationCreate(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    ref_type: str = Field(max_length=50)
    ref_id: uuid.UUID
    expires_at: datetime | None = None


class ReservationOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal
    ref_type: str
    ref_id: uuid.UUID
    status: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Movement ----------
class MovementOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    location_id: uuid.UUID | None
    type: str
    quantity: Decimal
    ref_type: str | None
    ref_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Alert ----------
class AlertCreate(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    threshold: Decimal = Field(ge=0)


class AlertOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    threshold: Decimal
    triggered_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}