import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Warehouse(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_warehouses_org_code"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    zones: Mapped[list["Zone"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")


class Zone(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("warehouse_id", "code", name="uq_zones_warehouse_code"),)

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="general", nullable=False)

    warehouse: Mapped[Warehouse] = relationship(back_populates="zones")
    locations: Mapped[list["Location"]] = relationship(back_populates="zone", cascade="all, delete-orphan")


class Location(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("zone_id", "code", name="uq_locations_zone_code"),)

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), default="shelf", nullable=False)
    capacity: Mapped[float | None] = mapped_column()

    zone: Mapped[Zone] = relationship(back_populates="locations")


class WarehouseTask(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "warehouse_tasks"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    ref_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()