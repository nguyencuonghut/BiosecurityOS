"""ORM models for Scorecard module (Sprint 03)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Computed,
    Date as SADate,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScorecardTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scorecard_template"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    farm_type: Mapped[str | None] = mapped_column(String(30))
    ownership_type: Mapped[str | None] = mapped_column(String(30))
    risk_profile: Mapped[str | None] = mapped_column(String(30))
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    effective_from: Mapped[date] = mapped_column(SADate, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(SADate)

    # Relationships
    sections: Mapped[list["ScorecardSection"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="ScorecardSection.display_order"
    )


class ScorecardSection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scorecard_section"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.scorecard_template.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    section_type: Mapped[str] = mapped_column(String(30), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # Relationships
    template: Mapped["ScorecardTemplate"] = relationship(back_populates="sections")
    items: Mapped[list["ScorecardItem"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="ScorecardItem.display_order"
    )


class ScorecardItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scorecard_item"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.scorecard_section.id", ondelete="CASCADE"), nullable=False
    )
    killer_metric_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.killer_metric_definition.id", ondelete="SET NULL"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_type: Mapped[str] = mapped_column(String(30), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    is_killer_related: Mapped[bool] = mapped_column(
        Boolean,
        Computed("killer_metric_definition_id IS NOT NULL", persisted=True),
    )
    threshold_warning: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    threshold_fail: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    guidance_text: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # Relationships
    section: Mapped["ScorecardSection"] = relationship(back_populates="items")
