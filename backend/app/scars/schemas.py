"""Pydantic schemas for Scar Memory module (Sprint 07)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# Scar Record
# ═══════════════════════════════════════════════════════════════════

VALID_SCAR_TYPES = ("outbreak", "hotspot", "repeated_breach", "near_miss", "structural_flaw")
VALID_CONFIDENCE_LEVELS = ("suspected", "probable", "confirmed")


class ScarCreate(BaseModel):
    farm_id: uuid.UUID
    floorplan_version_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
    scar_type: str = Field(..., max_length=30)
    title: str = Field(..., max_length=255)
    description: str
    source_of_risk: str | None = None
    confidence_level: str = Field(..., max_length=20)
    event_date: date | None = None
    x_percent: float | None = Field(None, ge=0, le=100)
    y_percent: float | None = Field(None, ge=0, le=100)
    recurrence_flag: bool = False


class ScarUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    source_of_risk: str | None = None
    confidence_level: str | None = Field(None, max_length=20)
    x_percent: float | None = Field(None, ge=0, le=100)
    y_percent: float | None = Field(None, ge=0, le=100)
    status: str | None = Field(None, max_length=30)


class ScarLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scar_id: uuid.UUID
    linked_object_type: str
    linked_object_id: uuid.UUID
    link_reason: str | None


class ScarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    floorplan_version_id: uuid.UUID | None
    area_id: uuid.UUID | None
    scar_type: str
    title: str
    description: str
    source_of_risk: str | None
    confidence_level: str
    event_date: date | None
    x_percent: float | None
    y_percent: float | None
    status: str
    recurrence_flag: bool
    recurrence_count: int
    created_by_user_id: uuid.UUID
    validated_by_user_id: uuid.UUID | None
    validated_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    links: list[ScarLinkOut] = []


class ScarListOut(BaseModel):
    """Lightweight schema for list endpoints (no links)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    scar_type: str
    title: str
    confidence_level: str
    event_date: date | None
    status: str
    recurrence_flag: bool
    recurrence_count: int
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════
# Scar Link
# ═══════════════════════════════════════════════════════════════════

VALID_LINK_TYPES = ("case", "task", "assessment", "attachment")


class ScarLinkCreate(BaseModel):
    linked_object_type: str = Field(..., max_length=30)
    linked_object_id: uuid.UUID
    link_reason: str | None = Field(None, max_length=100)


# ═══════════════════════════════════════════════════════════════════
# Scar Map
# ═══════════════════════════════════════════════════════════════════

class ScarMapItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scar_type: str
    title: str
    confidence_level: str
    x_percent: float | None
    y_percent: float | None
    status: str
    recurrence_count: int
    event_date: date | None
