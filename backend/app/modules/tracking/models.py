import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.shared.mixins import TenantMixin, UUIDPKMixin


class TrackingEvent(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "tracking_events"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc),
        nullable=False, index=True,
    )