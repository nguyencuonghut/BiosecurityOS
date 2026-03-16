"""Notification ORM model — used by killer_metrics and other modules."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models_base import Base, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification"

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(30))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="queued")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
