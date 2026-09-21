import uuid
from datetime import datetime

from pydantic import BaseModel, Field

CHANNELS = {"inapp", "email", "sms", "push"}


class NotificationCreate(BaseModel):
    user_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    channel: str = Field(max_length=20)
    template: str = Field(max_length=100)
    payload: dict = {}


class NotificationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    channel: str
    template: str
    payload_json: dict
    status: str
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationDeliveryOut(BaseModel):
    id: uuid.UUID
    notification_id: uuid.UUID
    provider: str
    provider_msg_id: str | None
    status: str
    error: str | None
    attempts: int
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}