"""Pydantic schemas for Floorplan / Digital Twin module (Sprint 07)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# Floorplan Version
# ═══════════════════════════════════════════════════════════════════

class FloorplanVersionCreate(BaseModel):
    title: str = Field(..., max_length=255)
    effective_from: date
    plan_file_attachment_id: uuid.UUID | None = None


class FloorplanVersionUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    effective_from: date | None = None
    effective_to: date | None = None
    plan_file_attachment_id: uuid.UUID | None = None


class FloorplanVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    version_no: int
    title: str
    effective_from: date
    effective_to: date | None
    plan_file_attachment_id: uuid.UUID | None
    status: str
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════════════
# Floorplan Marker
# ═══════════════════════════════════════════════════════════════════

class MarkerCreate(BaseModel):
    area_id: uuid.UUID | None = None
    marker_type: str = Field(..., max_length=50)
    label: str = Field(..., max_length=255)
    x_percent: float = Field(..., ge=0, le=100)
    y_percent: float = Field(..., ge=0, le=100)
    metadata_json: dict | None = None


class MarkerUpdate(BaseModel):
    area_id: uuid.UUID | None = None
    marker_type: str | None = Field(None, max_length=50)
    label: str | None = Field(None, max_length=255)
    x_percent: float | None = Field(None, ge=0, le=100)
    y_percent: float | None = Field(None, ge=0, le=100)
    metadata_json: dict | None = None


class MarkerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floorplan_version_id: uuid.UUID
    area_id: uuid.UUID | None
    marker_type: str
    label: str
    x_percent: float
    y_percent: float
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
