"""ORM models for Assessment module (Sprint 03)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id"), nullable=False
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.scorecard_template.id"), nullable=False
    )
    assessment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    assessment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    performed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id"), nullable=False
    )
    performed_by_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    hardware_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    process_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    behavior_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    monitoring_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    summary_note: Mapped[str | None] = mapped_column(Text)
    trust_gap_basis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    # Relationships
    item_results: Mapped[list["AssessmentItemResult"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["AssessmentAttachment"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentItemResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "assessment_item_result"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.assessment.id", ondelete="CASCADE"), nullable=False
    )
    scorecard_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.scorecard_item.id"), nullable=False
    )
    response_value_text: Mapped[str | None] = mapped_column(Text)
    response_value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    awarded_score: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    is_non_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    note: Mapped[str | None] = mapped_column(Text)
    area_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Relationships
    assessment: Mapped["Assessment"] = relationship(back_populates="item_results")


class AssessmentAttachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "assessment_attachment"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.assessment.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    area_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    caption: Mapped[str | None] = mapped_column(Text)

    # Relationships
    assessment: Mapped["Assessment"] = relationship(back_populates="attachments")
