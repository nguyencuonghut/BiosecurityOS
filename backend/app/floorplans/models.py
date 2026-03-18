"""ORM models for Floorplan / Digital Twin module (Sprint 07)."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FloorplanVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "floorplan_version"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="RESTRICT"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    plan_file_attachment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.attachment.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    markers: Mapped[list["FloorplanMarker"]] = relationship(
        back_populates="floorplan_version", cascade="all, delete-orphan"
    )


class FloorplanMarker(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "floorplan_marker"

    floorplan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.floorplan_version.id", ondelete="CASCADE"), nullable=False
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    marker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    x_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    y_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    floorplan_version: Mapped["FloorplanVersion"] = relationship(back_populates="markers")
