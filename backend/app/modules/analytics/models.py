import uuid
from datetime import date

from sqlalchemy import Date, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class FactOrdersDaily(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "fact_orders_daily"
    __table_args__ = (UniqueConstraint("organization_id", "date", name="uq_fact_orders_org_date"),)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    orders_count: Mapped[int] = mapped_column(default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(default=0, nullable=False)
    cancelled_count: Mapped[int] = mapped_column(default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)


class FactDeliveriesDaily(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "fact_deliveries_daily"
    __table_args__ = (UniqueConstraint("organization_id", "date", name="uq_fact_deliv_org_date"),)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    deliveries_count: Mapped[int] = mapped_column(default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_duration_s: Mapped[float | None] = mapped_column(Numeric(14, 2))


class FactDriverDaily(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "fact_driver_daily"
    __table_args__ = (
        UniqueConstraint("organization_id", "date", "driver_id", name="uq_fact_driver_org_date_drv"),
    )

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    deliveries_count: Mapped[int] = mapped_column(default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(default=0, nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)


class FactInventoryDaily(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "fact_inventory_daily"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "date", "product_id", "warehouse_id",
            name="uq_fact_inv_org_date_prod_wh",
        ),
    )

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    on_hand: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    reserved: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    low_stock_flag: Mapped[bool] = mapped_column(default=False, nullable=False)