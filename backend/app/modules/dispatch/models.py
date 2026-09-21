import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Assignment(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "assignments"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL")
    )
    score: Mapped[float] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="offered", nullable=False, index=True)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    assigned_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()


class DispatchEvent(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "dispatch_events"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    candidate_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL")
    )
    score: Mapped[float | None] = mapped_column(Numeric(10, 4))
    factors_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc), nullable=False, index=True
    )