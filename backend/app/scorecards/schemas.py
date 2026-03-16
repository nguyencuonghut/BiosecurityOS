"""Pydantic schemas for Scorecard module (template, section, item)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Scorecard Item ──────────────────────────────────────────────

class ScorecardItemCreate(BaseModel):
    code: str = Field(max_length=50)
    question_text: str
    response_type: str = Field(pattern=r"^(yes_no|score_0_5|option|numeric|text)$")
    max_score: Decimal = Field(ge=0)
    weight: Decimal = Field(ge=0)
    is_killer_related: bool = False
    threshold_warning: Decimal | None = Field(default=None, ge=0)
    threshold_fail: Decimal | None = Field(default=None, ge=0)
    guidance_text: str | None = None
    display_order: int = Field(default=1, gt=0)


class ScorecardItemUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    question_text: str | None = None
    response_type: str | None = Field(default=None, pattern=r"^(yes_no|score_0_5|option|numeric|text)$")
    max_score: Decimal | None = Field(default=None, ge=0)
    weight: Decimal | None = Field(default=None, ge=0)
    is_killer_related: bool | None = None
    threshold_warning: Decimal | None = Field(default=None, ge=0)
    threshold_fail: Decimal | None = Field(default=None, ge=0)
    guidance_text: str | None = None
    display_order: int | None = Field(default=None, gt=0)


class ScorecardItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    code: str
    question_text: str
    response_type: str
    max_score: Decimal
    weight: Decimal
    is_killer_related: bool
    threshold_warning: Decimal | None
    threshold_fail: Decimal | None
    guidance_text: str | None
    display_order: int


# ── Scorecard Section ──────────────────────────────────────────

class ScorecardSectionCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    section_type: str = Field(pattern=r"^(hardware|software|behavior|monitoring|other)$")
    weight: Decimal = Field(ge=0)
    display_order: int = Field(default=1, gt=0)


class ScorecardSectionUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    section_type: str | None = Field(default=None, pattern=r"^(hardware|software|behavior|monitoring|other)$")
    weight: Decimal | None = Field(default=None, ge=0)
    display_order: int | None = Field(default=None, gt=0)


class ScorecardSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: uuid.UUID
    code: str
    name: str
    section_type: str
    weight: Decimal
    display_order: int


class ScorecardSectionDetailOut(ScorecardSectionOut):
    """Section with nested items."""
    items: list[ScorecardItemOut] = []


# ── Scorecard Template ─────────────────────────────────────────

class ScorecardTemplateCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    farm_type: str | None = Field(default=None, max_length=30)
    ownership_type: str | None = Field(default=None, max_length=30)
    risk_profile: str | None = Field(default=None, max_length=30)
    version_no: int = Field(gt=0)
    effective_from: date
    effective_to: date | None = None


class ScorecardTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    farm_type: str | None = Field(default=None, max_length=30)
    ownership_type: str | None = Field(default=None, max_length=30)
    risk_profile: str | None = Field(default=None, max_length=30)
    effective_from: date | None = None
    effective_to: date | None = None


class ScorecardTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    farm_type: str | None
    ownership_type: str | None
    risk_profile: str | None
    version_no: int
    status: str
    effective_from: date
    effective_to: date | None
    created_at: datetime
    updated_at: datetime


class ScorecardTemplateDetailOut(ScorecardTemplateOut):
    """Template with nested sections and items."""
    sections: list[ScorecardSectionDetailOut] = []
