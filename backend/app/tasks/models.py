"""ORM models for Corrective Task module (Sprint 06)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class TaskType(str, enum.Enum):
    """Loại task khắc phục."""

    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    INSPECTION = "inspection"
    TRAINING = "training"
    CAPEX = "capex"


class TaskStatus(str, enum.Enum):
    """Trạng thái corrective task."""

    OPEN = "open"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    NEEDS_REWORK = "needs_rework"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CorrectiveTask(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, SoftDeleteMixin, Base):
    __tablename__ = "corrective_task"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.risk_case.id", ondelete="RESTRICT"), nullable=False
    )
    task_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="corrective_task_type_enum", schema="biosec",
               create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    source_rca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.rca_record.id", ondelete="SET NULL")
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="corrective_task_status_enum", schema="biosec",
               create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=text("'open'"),
    )
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_criteria: Mapped[str | None] = mapped_column(Text)
    evidence_requirement: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    assignees: Mapped[list["TaskAssignee"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["TaskReview"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    comments: Mapped[list["TaskComment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    task_attachments: Mapped[list["TaskAttachment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskAssignee(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "task_assignee"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.corrective_task.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), nullable=False
    )
    responsibility_type: Mapped[str] = mapped_column(String(30), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped["CorrectiveTask"] = relationship(back_populates="assignees")


class TaskAttachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "task_attachment"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.corrective_task.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.attachment.id", ondelete="RESTRICT"), nullable=False
    )
    upload_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    is_primary_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    caption: Mapped[str | None] = mapped_column(Text)

    task: Mapped["CorrectiveTask"] = relationship(back_populates="task_attachments")
    attachment = relationship("Attachment", lazy="raise")


class TaskReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "task_review"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.corrective_task.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    review_result: Mapped[str] = mapped_column(String(30), nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    next_action_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped["CorrectiveTask"] = relationship(back_populates="reviews")


class TaskComment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "task_comment"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.corrective_task.id", ondelete="CASCADE"), nullable=False
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    comment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task: Mapped["CorrectiveTask"] = relationship(back_populates="comments")
