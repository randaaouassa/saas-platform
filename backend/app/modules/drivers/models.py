import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Driver(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "drivers"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    license_no: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="offline", nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="driver", cascade="all, delete-orphan"
    )
    shifts: Mapped[list["DriverShift"]] = relationship(
        back_populates="driver", cascade="all, delete-orphan"
    )


class Vehicle(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "vehicles"

    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), index=True
    )
    plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    capacity_weight: Mapped[float | None] = mapped_column(Numeric(14, 3))
    capacity_volume: Mapped[float | None] = mapped_column(Numeric(14, 3))

    driver: Mapped[Driver | None] = relationship(back_populates="vehicles")


class DriverShift(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "driver_shifts"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    driver: Mapped[Driver] = relationship(back_populates="shifts")


class DriverPosition(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "driver_positions"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    heading: Mapped[float | None] = mapped_column()
    speed: Mapped[float | None] = mapped_column()
    recorded_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc),
        nullable=False, index=True,
    )