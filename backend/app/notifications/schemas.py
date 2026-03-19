"""Notification schemas (B10.4)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_user_id: uuid.UUID
    channel: str
    title: str
    body: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    status: str
    sent_at: datetime | None = None
    read_at: datetime | None = None


class NotificationCreate(BaseModel):
    """Internal schema — used by trigger rules, not exposed via API."""

    recipient_user_id: uuid.UUID
    channel: str = Field(default="in_app", pattern=r"^(in_app|email|webhook|sms)$")
    title: str = Field(..., max_length=255)
    body: str
    entity_type: str | None = Field(default=None, max_length=30)
    entity_id: uuid.UUID | None = None


class BulkReadRequest(BaseModel):
    notification_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)
