"""SQLAlchemy ORM models for Lesson Learned module (Sprint 08)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LessonLearned(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lesson_learned"

    lesson_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_context: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_summary: Mapped[str | None] = mapped_column(Text)
    action_summary: Mapped[str | None] = mapped_column(Text)
    outcome_summary: Mapped[str | None] = mapped_column(Text)
    recurrence_observed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    applicability_scope: Mapped[str | None] = mapped_column(Text)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    confirmed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    references: Mapped[list["LessonReference"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )
    tags: Mapped[list["SimilarityTag"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class LessonReference(Base):
    __tablename__ = "lesson_reference"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.lesson_learned.id", ondelete="CASCADE"), nullable=False
    )
    reference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    contribution_note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    lesson: Mapped["LessonLearned"] = relationship(back_populates="references")


class SimilarityTag(Base):
    __tablename__ = "similarity_tag"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.lesson_learned.id", ondelete="CASCADE"), nullable=False
    )
    tag_type: Mapped[str] = mapped_column(String(30), nullable=False)
    tag_value: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    lesson: Mapped["LessonLearned"] = relationship(back_populates="tags")
