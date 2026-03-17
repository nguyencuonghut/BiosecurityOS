"""Pydantic schemas for Corrective Task module (Sprint 06)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    task_type: str
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


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    task_no: str
    title: str
    description: str
    task_type: str
    source_rca_id: uuid.UUID | None
    area_id: uuid.UUID | None
    priority: str
    status: str
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


class ChangeTaskStatusRequest(BaseModel):
    target_status: str
    version: int
