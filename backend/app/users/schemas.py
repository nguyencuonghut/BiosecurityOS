"""Pydantic schemas for User module."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(max_length=100)
    full_name: str = Field(max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    region_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=150)
    status: str = Field(default="active", pattern=r"^(active|locked|archived)$")
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    region_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=150)
    status: str | None = Field(default=None, pattern=r"^(active|locked|archived)$")


class UserRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_id: uuid.UUID
    role_code: str | None = None
    role_name: str | None = None
    scope_region_id: uuid.UUID | None
    scope_farm_id: uuid.UUID | None
    effective_from: date | None
    effective_to: date | None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    email: str | None
    phone: str | None
    region_id: uuid.UUID | None
    farm_id: uuid.UUID | None
    title: str | None
    status: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    roles: list[UserRoleOut] = []


class UserRoleAssign(BaseModel):
    role_id: uuid.UUID
    scope_region_id: uuid.UUID | None = None
    scope_farm_id: uuid.UUID | None = None
    effective_from: date | None = None
    effective_to: date | None = None
