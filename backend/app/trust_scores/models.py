"""ORM model for Trust Score Snapshot (Sprint 04)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models_base import Base, UUIDPrimaryKeyMixin


class TrustScoreSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trust_score_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "farm_id", "source_self_assessment_id", "source_audit_assessment_id",
            name="uq_trust_score_snapshot_farm_self_audit",
        ),
        {"schema": "biosec"},
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="RESTRICT"), nullable=False
    )
    source_self_assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.assessment.id", ondelete="RESTRICT"), nullable=False
    )
    source_audit_assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.assessment.id", ondelete="RESTRICT"), nullable=False
    )
    trust_score: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    absolute_gap_score: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    severity_factor: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    snapshot_date: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
