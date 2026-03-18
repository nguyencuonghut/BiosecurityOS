"""Pydantic schemas for Lesson Learned module (Sprint 08)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

VALID_CONFIDENCE_LEVELS = ("suspected", "probable", "confirmed")
VALID_STATUSES = ("draft", "validated", "archived", "obsolete")
VALID_REFERENCE_TYPES = ("scar", "case", "task", "assessment")
VALID_TAG_TYPES = (
    "farm_type", "issue_type", "route_type", "season",
    "ownership_type", "risk_profile", "other",
)


# ═══════════════════════════════════════════════════════════════════
# Lesson CRUD
# ═══════════════════════════════════════════════════════════════════

class LessonCreate(BaseModel):
    title: str = Field(..., max_length=255)
    problem_context: str
    root_cause_summary: str | None = None
    action_summary: str | None = None
    outcome_summary: str | None = None
    recurrence_observed: bool = False
    applicability_scope: str | None = None
    confidence_level: str = Field(..., max_length=20)


class LessonUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    problem_context: str | None = None
    root_cause_summary: str | None = None
    action_summary: str | None = None
    outcome_summary: str | None = None
    recurrence_observed: bool | None = None
    applicability_scope: str | None = None
    confidence_level: str | None = Field(None, max_length=20)
    status: str | None = Field(None, max_length=30)


# ═══════════════════════════════════════════════════════════════════
# Reference
# ═══════════════════════════════════════════════════════════════════

class ReferenceCreate(BaseModel):
    reference_type: str = Field(..., max_length=30)
    reference_id: uuid.UUID
    contribution_note: str | None = None


class ReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    reference_type: str
    reference_id: uuid.UUID
    contribution_note: str | None


# ═══════════════════════════════════════════════════════════════════
# Similarity Tag
# ═══════════════════════════════════════════════════════════════════

class TagCreate(BaseModel):
    tag_type: str = Field(..., max_length=30)
    tag_value: str = Field(..., max_length=100)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    tag_type: str
    tag_value: str


# ═══════════════════════════════════════════════════════════════════
# Output
# ═══════════════════════════════════════════════════════════════════

class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_no: str
    title: str
    problem_context: str
    root_cause_summary: str | None
    action_summary: str | None
    outcome_summary: str | None
    recurrence_observed: bool
    applicability_scope: str | None
    confidence_level: str
    status: str
    confirmed_by_user_id: uuid.UUID | None
    confirmed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    references: list[ReferenceOut] = []
    tags: list[TagOut] = []


class LessonListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_no: str
    title: str
    problem_context: str
    confidence_level: str
    status: str
    recurrence_observed: bool
    applicability_scope: str | None
    created_at: datetime
