import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.mixins import TenantMixin, TimestampMixin, UUIDPKMixin


class Route(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "routes"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="planned", nullable=False, index=True)
    total_distance_m: Mapped[float | None] = mapped_column(Numeric(14, 2))
    total_duration_s: Mapped[float | None] = mapped_column(Numeric(14, 2))

    stops: Mapped[list["RouteStop"]] = relationship(
        back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.sequence"
    )


class RouteStop(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("route_id", "sequence", name="uq_route_stops_route_seq"),)

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    eta: Mapped[datetime | None] = mapped_column()
    arrived_at: Mapped[datetime | None] = mapped_column()
    departed_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    route: Mapped[Route] = relationship(back_populates="stops")


class RouteRecalculation(UUIDPKMixin, TenantMixin, Base):
    __tablename__ = "route_recalculations"

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    before_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    after_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(__import__("datetime").timezone.utc), nullable=False, index=True
    )