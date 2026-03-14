import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models. All tables live in 'biosec' schema."""

    __table_args__ = {"schema": "biosec"}


class TimestampMixin:
    """Adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UUIDPrimaryKeyMixin:
    """Adds UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


class VersionMixin:
    """Adds version column for optimistic locking."""

    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)


class SoftDeleteMixin:
    """Adds archived_at column for soft delete."""

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
