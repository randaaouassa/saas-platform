import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Delivery(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "deliveries"

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    pickup_location: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column()
    pickup_lng: Mapped[float | None] = mapped_column()
    dropoff_location: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    dropoff_lat: Mapped[float | None] = mapped_column()
    dropoff_lng: Mapped[float | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column()
    delivered_at: Mapped[datetime | None] = mapped_column()
    failed_reason: Mapped[str | None] = mapped_column(String(500))
    public_token: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)

    packages: Mapped[list["Package"]] = relationship(
        back_populates="delivery", cascade="all, delete-orphan"
    )


class Package(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "packages"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_packages_org_code"),)

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    weight: Mapped[float | None] = mapped_column(Numeric(14, 3))
    length: Mapped[float | None] = mapped_column(Numeric(14, 3))
    width: Mapped[float | None] = mapped_column(Numeric(14, 3))
    height: Mapped[float | None] = mapped_column(Numeric(14, 3))
    volume: Mapped[float | None] = mapped_column(Numeric(14, 3))

    delivery: Mapped[Delivery] = relationship(back_populates="packages")


class DeliveryStatusHistory(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "delivery_status_history"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc), nullable=False, index=True
    )


class ProofOfDelivery(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "proof_of_delivery"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(500))
    signer_name: Mapped[str | None] = mapped_column(String(255))
    signature_s3_key: Mapped[str | None] = mapped_column(String(500))
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    captured_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc), nullable=False
    )