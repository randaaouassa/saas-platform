import uuid
from datetime import datetime

from pydantic import BaseModel


class WSMessage(BaseModel):
    topic: str
    event: str
    data: dict
    at: datetime | None = None


class TrackingEventOut(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    type: str
    lat: float | None
    lng: float | None
    payload_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicTrackingStatus(BaseModel):
    delivery_id: uuid.UUID
    status: str
    dropoff_location: str
    dropoff_lat: float | None
    dropoff_lng: float | None
    scheduled_at: datetime | None
    delivered_at: datetime | None
    history: list[TrackingEventOut]