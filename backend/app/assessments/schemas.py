"""Pydantic schemas for Assessment module."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.assessments.models import AssessmentType

# Vietnamese labels — mapping thực hiện tại BE
ASSESSMENT_TYPE_LABELS: dict[str, str] = {
    AssessmentType.SELF: "Tự đánh giá",
    AssessmentType.SCHEDULED_AUDIT: "Đánh giá định kỳ",
    AssessmentType.SPOT: "Đánh giá đột xuất",
    AssessmentType.BLIND: "Đánh giá ẩn danh",
    AssessmentType.INCIDENT_REVIEW: "Đánh giá sau sự cố",
}


# ── Assessment Item Result ──────────────────────────────────────

class AssessmentItemResultIn(BaseModel):
    scorecard_item_id: uuid.UUID
    response_value_text: str | None = None
    response_value_numeric: Decimal | None = Field(default=None, ge=0)
    awarded_score: Decimal = Field(ge=0)
    is_non_compliant: bool = False
    note: str | None = None
    area_id: uuid.UUID | None = None
    evidence_required: bool = False


class AssessmentItemResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    scorecard_item_id: uuid.UUID
    response_value_text: str | None
    response_value_numeric: Decimal | None
    awarded_score: Decimal
    is_non_compliant: bool
    note: str | None
    area_id: uuid.UUID | None
    evidence_required: bool


class BulkUpsertRequest(BaseModel):
    items: list[AssessmentItemResultIn] = Field(min_length=1)


# ── Assessment Attachment ───────────────────────────────────────

class AssessmentAttachmentCreate(BaseModel):
    attachment_id: uuid.UUID
    area_id: uuid.UUID | None = None
    caption: str | None = None


class AssessmentAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    attachment_id: uuid.UUID
    area_id: uuid.UUID | None
    caption: str | None


# ── Assessment ──────────────────────────────────────────────────

class AssessmentCreate(BaseModel):
    farm_id: uuid.UUID
    template_id: uuid.UUID
    assessment_type: AssessmentType
    assessment_date: datetime | None = None


class AssessmentUpdate(BaseModel):
    assessment_type: AssessmentType | None = None
    assessment_date: datetime | None = None
    summary_note: str | None = None


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str | None = None
    template_id: uuid.UUID
    assessment_type: AssessmentType
    assessment_date: datetime
    performed_by_user_id: uuid.UUID
    performed_by_name_snapshot: str
    overall_score: Decimal | None
    hardware_score: Decimal | None
    process_score: Decimal | None
    behavior_score: Decimal | None
    monitoring_score: Decimal | None
    status: str
    summary_note: str | None
    trust_gap_basis_id: uuid.UUID | None
    version: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def assessment_type_label(self) -> str:
        """Nhãn tiếng Việt được map tại BE."""
        return ASSESSMENT_TYPE_LABELS.get(self.assessment_type, self.assessment_type.value)


class AssessmentDetailOut(AssessmentOut):
    item_results: list[AssessmentItemResultOut] = []
    attachments: list[AssessmentAttachmentOut] = []


# ── Spider Chart ────────────────────────────────────────────────

class SpiderAxisOut(BaseModel):
    code: str
    label: str
    score: Decimal | None


class SpiderChartOut(BaseModel):
    farm_id: uuid.UUID
    assessment_id: uuid.UUID
    axes: list[SpiderAxisOut]
