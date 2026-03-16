"""ORM models for authentication & authorization (Sprint 01)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Region(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "region"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), server_default="active", nullable=False)

    farms: Mapped[list["Farm"]] = relationship(back_populates="region")


class Farm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farm"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    farm_type: Mapped[str] = mapped_column(String(30), nullable=False)
    ownership_type: Mapped[str] = mapped_column(String(30), nullable=False)
    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.region.id", ondelete="RESTRICT"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    capacity_headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operational_status: Mapped[str] = mapped_column(String(30), server_default="active", nullable=False)
    baseline_risk_level: Mapped[str] = mapped_column(String(30), server_default="medium", nullable=False)
    structural_risk_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    region: Mapped["Region"] = relationship(back_populates="farms")
    areas: Mapped[list["FarmArea"]] = relationship(back_populates="farm")
    routes: Mapped[list["FarmRoute"]] = relationship(back_populates="farm")
    external_risk_points: Mapped[list["ExternalRiskPoint"]] = relationship(back_populates="farm")


class AppUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "app_user"

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.region.id", ondelete="SET NULL")
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), server_default="active", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    credential: Mapped["AppUserCredential | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["AppRefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AppUserCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "app_user_credential"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["AppUser"] = relationship(back_populates="credential")


class AppRefreshToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "app_refresh_token"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"), nullable=False)

    user: Mapped["AppUser"] = relationship(back_populates="refresh_tokens")


class AppRole(Base):
    __tablename__ = "app_role"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class AppPermission(Base):
    __tablename__ = "app_permission"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permission"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_role.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_permission.id", ondelete="CASCADE"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(server_default=text("now()"), nullable=False)

    role: Mapped["AppRole"] = relationship(back_populates="role_permissions")
    permission: Mapped["AppPermission"] = relationship()


class UserRole(Base):
    __tablename__ = "user_role"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_role.id", ondelete="CASCADE"), nullable=False
    )
    scope_region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.region.id", ondelete="SET NULL")
    )
    scope_farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="SET NULL")
    )
    effective_from: Mapped[datetime | None] = mapped_column(Date)
    effective_to: Mapped[datetime | None] = mapped_column(Date)

    user: Mapped["AppUser"] = relationship(back_populates="user_roles")
    role: Mapped["AppRole"] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.app_user.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(server_default=text("now()"), nullable=False)


class LookupCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lookup_code"

    group_code: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
