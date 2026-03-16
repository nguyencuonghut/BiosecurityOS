"""Pydantic schemas for Killer Metrics module (Sprint 04)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Definition schemas ──

class KillerMetricDefinitionCreate(BaseModel):
    code: str
    name: str
    description: str
    severity_level: str
    default_case_priority: str
    active_flag: bool = True


class KillerMetricDefinitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    severity_level: str | None = None
    default_case_priority: str | None = None
    active_flag: bool | None = None


class KillerMetricDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str
    severity_level: str
    default_case_priority: str
    active_flag: bool


# ── Event schemas ──

class KillerMetricEventCreate(BaseModel):
    farm_id: uuid.UUID
    area_id: uuid.UUID | None = None
    definition_id: uuid.UUID
    event_at: datetime | None = None
    summary: str
    source_type: str


class KillerMetricEventUpdate(BaseModel):
    summary: str | None = None
    status: str | None = None
    version: int


class DefinitionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    severity_level: str
    default_case_priority: str


class KillerMetricEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    area_id: uuid.UUID | None
    definition_id: uuid.UUID
    definition: DefinitionBrief | None = None
    event_at: datetime
    detected_by_user_id: uuid.UUID
    detected_by_name: str | None = None
    source_type: str
    summary: str
    status: str
    required_case_flag: bool
    version: int
    created_at: datetime
    updated_at: datetime
