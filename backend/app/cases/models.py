"""ORM models for Risk Case & RCA module (Sprint 05)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class RiskCase(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, SoftDeleteMixin, Base):
    __tablename__ = "risk_case"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="RESTRICT"), nullable=False
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    case_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    case_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.assessment.id", ondelete="SET NULL")
    )
    source_killer_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.killer_metric_event.id", ondelete="SET NULL")
    )
    source_scar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    current_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="open")
    assigned_expert_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    first_response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closure_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    participants: Mapped[list["CaseParticipant"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    rca_records: Mapped[list["RcaRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class CaseParticipant(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "case_participant"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.risk_case.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), nullable=False
    )
    role_in_case: Mapped[str] = mapped_column(String(30), nullable=False)

    case: Mapped["RiskCase"] = relationship(back_populates="participants")


class RcaRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rca_record"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.risk_case.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    impact_scope: Mapped[str | None] = mapped_column(Text)
    direct_cause: Mapped[str | None] = mapped_column(Text)
    system_cause: Mapped[str | None] = mapped_column(Text)
    behavioral_cause: Mapped[str | None] = mapped_column(Text)
    structural_cause: Mapped[str | None] = mapped_column(Text)
    monitoring_cause: Mapped[str | None] = mapped_column(Text)
    external_factor: Mapped[str | None] = mapped_column(Text)
    conclusion_confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    analyzed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped["RiskCase"] = relationship(back_populates="rca_records")
    factors: Mapped[list["RcaFactor"]] = relationship(
        back_populates="rca_record", cascade="all, delete-orphan"
    )


class RcaFactor(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rca_factor"

    rca_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.rca_record.id", ondelete="CASCADE"), nullable=False
    )
    factor_group: Mapped[str] = mapped_column(String(30), nullable=False)
    factor_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False)

    rca_record: Mapped["RcaRecord"] = relationship(back_populates="factors")
