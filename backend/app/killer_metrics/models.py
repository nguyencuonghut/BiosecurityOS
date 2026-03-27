"""ORM models for Killer Metrics module (Sprint 04)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KillerMetricDefinition(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "killer_metric_definition"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="both"
    )  # 'scorecard_item' | 'field_report' | 'both'
    severity_level: Mapped[str] = mapped_column(String(20), nullable=False)
    default_case_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    events: Mapped[list["KillerMetricEvent"]] = relationship(back_populates="definition")


class KillerMetricEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "killer_metric_event"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="RESTRICT"), nullable=False
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.killer_metric_definition.id", ondelete="RESTRICT"), nullable=False
    )
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    detected_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # 'assessment' | 'field_report'
    source_assessment_item_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("biosec.assessment_item_result.id", ondelete="SET NULL"),
    )  # nullable; bắt buộc khi source_type='assessment'
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="open"
    )  # 'open' | 'under_review' | 'controlled' | 'closed' | 'rejected'
    required_case_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    definition: Mapped["KillerMetricDefinition"] = relationship(back_populates="events")
    event_attachments: Mapped[list["KillerEventAttachment"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class KillerEventAttachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "killer_event_attachment"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.killer_metric_event.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.attachment.id", ondelete="CASCADE"), nullable=False
    )
    caption: Mapped[str | None] = mapped_column(Text)

    event: Mapped["KillerMetricEvent"] = relationship(back_populates="event_attachments")
    attachment = relationship("Attachment", lazy="raise")
