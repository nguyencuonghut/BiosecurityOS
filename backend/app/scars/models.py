"""ORM models for Scar Memory module (Sprint 07)."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScarRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scar_record"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="RESTRICT"), nullable=False
    )
    floorplan_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.floorplan_version.id", ondelete="SET NULL")
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    scar_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_of_risk: Mapped[str | None] = mapped_column(Text)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date)
    x_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    y_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="active")
    recurrence_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    validated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    links: Mapped[list["ScarLink"]] = relationship(
        back_populates="scar", cascade="all, delete-orphan"
    )


class ScarLink(Base):
    __tablename__ = "scar_link"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.scar_record.id", ondelete="CASCADE"), nullable=False
    )
    linked_object_type: Mapped[str] = mapped_column(String(30), nullable=False)
    linked_object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    link_reason: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    scar: Mapped["ScarRecord"] = relationship(back_populates="links")
