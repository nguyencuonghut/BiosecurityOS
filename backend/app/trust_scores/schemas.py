"""Pydantic schemas for Trust Score module (Sprint 04)."""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TrustScoreCalculateRequest(BaseModel):
    farm_id: uuid.UUID
    self_assessment_id: uuid.UUID
    audit_assessment_id: uuid.UUID


class FormulaBreakdown(BaseModel):
    step1_gap: float
    step2_abs_gap: float
    step3_penalty: float
    step4_severity_factor: float
    step5_trust_score: float


class TrustScoreCalculateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    source_self_assessment_id: uuid.UUID
    source_audit_assessment_id: uuid.UUID
    self_overall_score: float
    audit_overall_score: float
    gap: float
    abs_gap: float
    penalty: float
    trust_score: float
    absolute_gap_score: float
    severity_factor: float
    snapshot_date: date
    formula_breakdown: FormulaBreakdown
    note: str | None = None


class TrustScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    source_self_assessment_id: uuid.UUID
    source_audit_assessment_id: uuid.UUID
    trust_score: Decimal
    absolute_gap_score: Decimal
    severity_factor: Decimal | None
    snapshot_date: date
    note: str | None = None


class TrustScoreLatestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    trust_score: Decimal
    absolute_gap_score: Decimal
    severity_factor: Decimal | None
    snapshot_date: date
    note: str | None = None
    # Comparison to previous
    previous_trust_score: Decimal | None = None
    previous_date: date | None = None
    change: float | None = None
    trend: str | None = None
