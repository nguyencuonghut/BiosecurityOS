"""Pydantic schemas for Risk Case & RCA module (Sprint 05)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ═══════════════════════════════════════════════════════════════════
# Risk Case schemas
# ═══════════════════════════════════════════════════════════════════

class CaseCreate(BaseModel):
    farm_id: uuid.UUID
    area_id: uuid.UUID | None = None
    case_type: str
    title: str
    summary: str
    source_assessment_id: uuid.UUID | None = None
    source_killer_event_id: uuid.UUID | None = None
    source_scar_id: uuid.UUID | None = None
    priority: str
    severity: str


class CaseUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    priority: str | None = None
    severity: str | None = None
    first_response_due_at: datetime | None = None
    closure_due_at: datetime | None = None
    version: int


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    area_id: uuid.UUID | None
    case_no: str
    case_type: str
    title: str
    summary: str
    source_assessment_id: uuid.UUID | None
    source_killer_event_id: uuid.UUID | None
    source_scar_id: uuid.UUID | None
    priority: str
    severity: str
    current_status: str
    assigned_expert_user_id: uuid.UUID | None
    assigned_expert_name: str | None = None
    first_response_due_at: datetime | None
    closure_due_at: datetime | None
    opened_at: datetime
    closed_at: datetime | None
    version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssignExpertRequest(BaseModel):
    expert_user_id: uuid.UUID


class ChangeStatusRequest(BaseModel):
    target_status: str
    version: int


# ═══════════════════════════════════════════════════════════════════
# Case Participant schemas
# ═══════════════════════════════════════════════════════════════════

class CaseParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    role_in_case: str


# ═══════════════════════════════════════════════════════════════════
# RCA Record schemas
# ═══════════════════════════════════════════════════════════════════

class RcaRecordCreate(BaseModel):
    method: str
    problem_statement: str
    impact_scope: str | None = None
    direct_cause: str | None = None
    system_cause: str | None = None
    behavioral_cause: str | None = None
    structural_cause: str | None = None
    monitoring_cause: str | None = None
    external_factor: str | None = None
    conclusion_confidence: str


class RcaRecordUpdate(BaseModel):
    method: str | None = None
    problem_statement: str | None = None
    impact_scope: str | None = None
    direct_cause: str | None = None
    system_cause: str | None = None
    behavioral_cause: str | None = None
    structural_cause: str | None = None
    monitoring_cause: str | None = None
    external_factor: str | None = None
    conclusion_confidence: str | None = None


class RcaFactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rca_record_id: uuid.UUID
    factor_group: str
    factor_text: str
    confidence_level: str
    is_primary: bool


class RcaRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    method: str
    problem_statement: str
    impact_scope: str | None
    direct_cause: str | None
    system_cause: str | None
    behavioral_cause: str | None
    structural_cause: str | None
    monitoring_cause: str | None
    external_factor: str | None
    conclusion_confidence: str
    analyzed_by_user_id: uuid.UUID
    analyzed_at: datetime
    approved_by_user_id: uuid.UUID | None
    approved_at: datetime | None
    factors: list[RcaFactorOut] = []


# ═══════════════════════════════════════════════════════════════════
# RCA Factor schemas
# ═══════════════════════════════════════════════════════════════════

class RcaFactorCreate(BaseModel):
    factor_group: str
    factor_text: str
    confidence_level: str
    is_primary: bool = False


class RcaFactorUpdate(BaseModel):
    factor_group: str | None = None
    factor_text: str | None = None
    confidence_level: str | None = None
    is_primary: bool | None = None


# ═══════════════════════════════════════════════════════════════════
# Timeline schema
# ═══════════════════════════════════════════════════════════════════

class TimelineEntry(BaseModel):
    event_type: str
    occurred_at: datetime
    actor: str | None = None
    detail: str
