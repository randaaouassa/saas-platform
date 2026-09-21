import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# ---------- Customer ----------
class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str = Field(default="", max_length=500)
    lat: float | None = None
    lng: float | None = None
    external_ref: str | None = Field(default=None, max_length=100)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    lat: float | None = None
    lng: float | None = None
    external_ref: str | None = Field(default=None, max_length=100)


class CustomerOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    address: str
    lat: float | None
    lng: float | None
    external_ref: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Order item ----------
class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0, default=Decimal(0))


class OrderItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


# ---------- Order ----------
class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    number: str = Field(min_length=1, max_length=50)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str = Field(default="", max_length=1000)
    warehouse_id: uuid.UUID  # where to reserve stock from
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    number: str
    status: str
    currency: str
    total_amount: Decimal
    notes: str
    placed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str = Field(max_length=30)
    reason: str | None = Field(default=None, max_length=255)


class OrderStatusHistoryOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_id: uuid.UUID | None
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}