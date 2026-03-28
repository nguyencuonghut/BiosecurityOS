"""Pydantic schemas for Corrective Task module (Sprint 06)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from app.tasks.models import TaskStatus, TaskType


TASK_TYPE_LABELS: dict[str, str] = {
    TaskType.CORRECTIVE:  "Khắc phục",
    TaskType.PREVENTIVE:  "Phòng ngừa",
    TaskType.INSPECTION:  "Kiểm tra",
    TaskType.TRAINING:    "Đào tạo",
    TaskType.CAPEX:       "Đầu tư (CapEx)",
}

TASK_STATUS_LABELS: dict[str, str] = {
    TaskStatus.OPEN:           "Mở mới",
    TaskStatus.ACCEPTED:       "Đã nhận",
    TaskStatus.IN_PROGRESS:    "Đang thực hiện",
    TaskStatus.PENDING_REVIEW: "Chờ duyệt",
    TaskStatus.NEEDS_REWORK:   "Cần làm lại",
    TaskStatus.CLOSED:         "Đã đóng",
    TaskStatus.CANCELLED:      "Đã hủy",
}


# ═══════════════════════════════════════════════════════════════════
# Task Assignee schemas
# ═══════════════════════════════════════════════════════════════════

class TaskAssigneeInput(BaseModel):
    user_id: uuid.UUID
    responsibility_type: str


class TaskAssigneeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    responsibility_type: str
    accepted_at: datetime | None


# ═══════════════════════════════════════════════════════════════════
# Task Attachment schemas
# ═══════════════════════════════════════════════════════════════════

class TaskAttachmentCreate(BaseModel):
    attachment_id: uuid.UUID
    upload_stage: str
    is_primary_evidence: bool = False
    caption: str | None = None


class TaskAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    attachment_id: uuid.UUID
    upload_stage: str
    is_primary_evidence: bool
    caption: str | None


class TaskAttachmentDetailOut(TaskAttachmentOut):
    """Enriched schema with nested attachment metadata (file name, mime, size)."""
    file_name_original: str | None = None
    mime_type: str | None = None
    file_size_bytes: int | None = None
    captured_at: datetime | None = None
    uploaded_at: datetime | None = None

    @model_validator(mode="wrap")
    @classmethod
    def _extract_attachment(cls, values, handler):
        """Extract fields from the nested .attachment relationship when using from_attributes."""
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


# ═══════════════════════════════════════════════════════════════════
# Task Review schemas
# ═══════════════════════════════════════════════════════════════════

class TaskReviewCreate(BaseModel):
    review_result: str
    review_note: str | None = None
    next_action_due_at: datetime | None = None


class TaskReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    reviewer_user_id: uuid.UUID
    review_result: str
    review_note: str | None
    reviewed_at: datetime
    next_action_due_at: datetime | None


# ═══════════════════════════════════════════════════════════════════
# Task Comment schemas
# ═══════════════════════════════════════════════════════════════════

class TaskCommentCreate(BaseModel):
    comment_text: str
    comment_type: str = "note"


class TaskCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    author_user_id: uuid.UUID
    comment_text: str
    comment_type: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════
# Corrective Task schemas
# ═══════════════════════════════════════════════════════════════════

class TaskCreate(BaseModel):
    case_id: uuid.UUID
    title: str
    description: str
    task_type: TaskType
    source_rca_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
    priority: str
    sla_due_at: datetime | None = None
    completion_due_at: datetime | None = None
    completion_criteria: str | None = None
    evidence_requirement: str | None = None
    assignees: list[TaskAssigneeInput] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    sla_due_at: datetime | None = None
    completion_due_at: datetime | None = None
    completion_criteria: str | None = None
    evidence_requirement: str | None = None
    version: int


class TaskListOut(BaseModel):
    """Lightweight schema for list endpoints (no nested reviews/comments/attachments)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    task_no: str
    title: str
    description: str
    task_type: TaskType
    source_rca_id: uuid.UUID | None
    area_id: uuid.UUID | None
    priority: str
    status: TaskStatus
    sla_due_at: datetime | None
    completion_due_at: datetime | None
    completion_criteria: str | None
    evidence_requirement: str | None
    created_by_user_id: uuid.UUID
    closed_by_user_id: uuid.UUID | None
    closed_at: datetime | None
    version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    assignees: list[TaskAssigneeOut] = []

    @computed_field
    @property
    def task_type_label(self) -> str:
        return TASK_TYPE_LABELS.get(self.task_type, self.task_type.value)

    @computed_field
    @property
    def status_label(self) -> str:
        return TASK_STATUS_LABELS.get(self.status, self.status.value)


class TaskOut(TaskListOut):
    """Full schema for detail endpoint (includes nested reviews/comments/attachments)."""
    reviews: list[TaskReviewOut] = []
    comments: list[TaskCommentOut] = []
    task_attachments: list[TaskAttachmentDetailOut] = []


class ChangeTaskStatusRequest(BaseModel):
    target_status: TaskStatus
    version: int
