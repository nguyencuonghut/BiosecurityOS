"""Pydantic schemas for Killer Metrics module (Sprint 04)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


# ── Definition schemas ──

class KillerMetricDefinitionCreate(BaseModel):
    code: str
    name: str
    description: str
    source_type: Literal["scorecard_item", "field_report", "both"] = "both"
    severity_level: str
    default_case_priority: str
    active_flag: bool = True


class KillerMetricDefinitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    source_type: Literal["scorecard_item", "field_report", "both"] | None = None
    severity_level: str | None = None
    default_case_priority: str | None = None
    active_flag: bool | None = None


class KillerMetricDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str
    source_type: str
    severity_level: str
    default_case_priority: str
    active_flag: bool


# ── Event schemas ──

VALID_EVENT_SOURCE_TYPES = {"assessment", "field_report"}
VALID_EVENT_STATUSES = {"open", "under_review", "controlled", "closed", "rejected"}


class KillerMetricEventCreate(BaseModel):
    farm_id: uuid.UUID
    area_id: uuid.UUID | None = None
    definition_id: uuid.UUID
    event_at: datetime | None = None
    summary: str
    source_type: Literal["assessment", "field_report"]
    source_assessment_item_result_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_source_consistency(self):
        if self.source_type == "assessment" and self.source_assessment_item_result_id is None:
            raise ValueError(
                "source_assessment_item_result_id bắt buộc khi source_type là 'assessment'."
            )
        if self.source_type == "field_report" and self.source_assessment_item_result_id is not None:
            raise ValueError(
                "source_assessment_item_result_id phải để trống khi source_type là 'field_report'."
            )
        return self


class KillerMetricEventUpdate(BaseModel):
    summary: str | None = None
    status: str | None = None
    version: int


class DefinitionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    source_type: str
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
    source_assessment_item_result_id: uuid.UUID | None = None
    summary: str
    status: str
    required_case_flag: bool
    version: int
    created_at: datetime
    updated_at: datetime


# ── Event Attachment schemas ──

class KillerEventAttachmentCreate(BaseModel):
    attachment_id: uuid.UUID
    caption: str | None = None


class KillerEventAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    attachment_id: uuid.UUID
    caption: str | None


class KillerEventAttachmentDetailOut(KillerEventAttachmentOut):
    """Enriched with nested attachment metadata."""
    file_name_original: str | None = None
    mime_type: str | None = None
    file_size_bytes: int | None = None
    captured_at: datetime | None = None
    uploaded_at: datetime | None = None

    @model_validator(mode="wrap")
    @classmethod
    def _extract_attachment(cls, values, handler):
        if hasattr(values, "attachment") and values.attachment is not None:
            att = values.attachment
            obj = handler(values)
            obj.file_name_original = getattr(att, "file_name_original", None)
            obj.mime_type = getattr(att, "mime_type", None)
            obj.file_size_bytes = getattr(att, "file_size_bytes", None)
            obj.captured_at = getattr(att, "captured_at", None)
            obj.uploaded_at = getattr(att, "uploaded_at", None)
            return obj
        return handler(values)
