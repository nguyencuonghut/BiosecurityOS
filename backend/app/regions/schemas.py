"""Pydantic schemas for Region module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegionCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    manager_user_id: uuid.UUID | None = None
    status: str = Field(default="active", pattern=r"^(active|inactive)$")


class RegionUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    manager_user_id: uuid.UUID | None = None
    status: str | None = Field(default=None, pattern=r"^(active|inactive)$")


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    manager_user_id: uuid.UUID | None
    status: str
    created_at: datetime
    updated_at: datetime
