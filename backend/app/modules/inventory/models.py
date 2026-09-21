import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Product(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),)

    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="pc", nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), index=True)
    weight: Mapped[float | None] = mapped_column(Numeric(14, 3))
    length: Mapped[float | None] = mapped_column(Numeric(14, 3))
    width: Mapped[float | None] = mapped_column(Numeric(14, 3))
    height: Mapped[float | None] = mapped_column(Numeric(14, 3))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Stock(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", "location_id", name="uq_stock_prod_wh_loc"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)


class StockMovement(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "stock_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL")
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(50))
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc), nullable=False, index=True
    )


class StockReservation(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "stock_reservations"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    ref_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ref_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column()


class StockAlert(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "stock_alerts"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    threshold: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    triggered_at: Mapped[datetime | None] = mapped_column()
    resolved_at: Mapped[datetime | None] = mapped_column()