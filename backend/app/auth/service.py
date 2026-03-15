"""Auth service — login, refresh, logout logic with password lockout (B01.4 + B01.5)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import AppPermission, AppRefreshToken, AppUser, AppUserCredential, RolePermission, UserRole
from app.auth.schemas import MeResponse, RoleOut, TokenResponse, UserBrief
from app.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.config import settings
from app.shared.exceptions import ForbiddenException, NotFoundException, UnauthorizedException

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


async def _get_user_permissions(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
    """Fetch distinct permission codes for user through user_role → role_permission → permission."""
    stmt = (
        select(AppPermission.code)
        .join(RolePermission, RolePermission.permission_id == AppPermission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(
            UserRole.user_id == user_id,
            (UserRole.effective_from.is_(None)) | (UserRole.effective_from <= datetime.now(UTC).date()),
            (UserRole.effective_to.is_(None)) | (UserRole.effective_to >= datetime.now(UTC).date()),
        )
        .distinct()
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_user_roles(db: AsyncSession, user_id: uuid.UUID) -> list[RoleOut]:
    """Fetch roles assigned to user."""
    from app.auth.models import AppRole

    stmt = (
        select(AppRole)
        .join(UserRole, UserRole.role_id == AppRole.id)
        .where(
            UserRole.user_id == user_id,
            (UserRole.effective_from.is_(None)) | (UserRole.effective_from <= datetime.now(UTC).date()),
            (UserRole.effective_to.is_(None)) | (UserRole.effective_to >= datetime.now(UTC).date()),
        )
    )
    result = await db.execute(stmt)
    return [RoleOut.model_validate(r) for r in result.scalars().all()]


async def login(
    db: AsyncSession,
    username: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    # Find user
    stmt = select(AppUser).where(AppUser.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("Sai tên đăng nhập hoặc mật khẩu.")

    if user.status != "active":
        raise ForbiddenException("Tài khoản đã bị khóa hoặc lưu trữ.")

    # Get credential
    cred_stmt = select(AppUserCredential).where(AppUserCredential.user_id == user.id)
    cred_result = await db.execute(cred_stmt)
    credential = cred_result.scalar_one_or_none()
    if not credential:
        raise UnauthorizedException("Sai tên đăng nhập hoặc mật khẩu.")

    # Check lockout (B01.5)
    if credential.locked_until and credential.locked_until > datetime.now(UTC):
        remaining = int((credential.locked_until - datetime.now(UTC)).total_seconds())
        raise ForbiddenException(f"Tài khoản tạm khóa. Thử lại sau {remaining} giây.")

    # Verify password
    if not verify_password(password, credential.password_hash):
        credential.failed_attempts += 1
        if credential.failed_attempts >= MAX_FAILED_ATTEMPTS:
            credential.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
        await db.commit()
        raise UnauthorizedException("Sai tên đăng nhập hoặc mật khẩu.")

    # Reset failed attempts on success
    credential.failed_attempts = 0
    credential.locked_until = None

    # Update last login
    user.last_login_at = datetime.now(UTC)

    # Get permissions for token
    permissions = await _get_user_permissions(db, user.id)

    # Create tokens
    access_token, expires = create_access_token(user.id, permissions)
    raw_refresh = generate_refresh_token()
    refresh_token = AppRefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(refresh_token)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh(
    db: AsyncSession,
    raw_refresh_token: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    token_hash = hash_refresh_token(raw_refresh_token)
    stmt = (
        select(AppRefreshToken)
        .where(
            AppRefreshToken.token_hash == token_hash,
            AppRefreshToken.revoked_at.is_(None),
            AppRefreshToken.expires_at > datetime.now(UTC),
        )
    )
    result = await db.execute(stmt)
    rt = result.scalar_one_or_none()
    if not rt:
        raise UnauthorizedException("Refresh token không hợp lệ hoặc đã hết hạn.")

    # Revoke old token (rotate)
    rt.revoked_at = datetime.now(UTC)

    # Load user
    user_stmt = select(AppUser).where(AppUser.id == rt.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user or user.status != "active":
        raise ForbiddenException("Tài khoản không hoạt động.")

    # Create new tokens
    permissions = await _get_user_permissions(db, user.id)
    access_token, expires = create_access_token(user.id, permissions)
    raw_new_refresh = generate_refresh_token()
    new_rt = AppRefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_new_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(new_rt)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    stmt = (
        select(AppRefreshToken)
        .where(
            AppRefreshToken.token_hash == token_hash,
            AppRefreshToken.revoked_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked_at = datetime.now(UTC)
        await db.flush()


async def get_me(db: AsyncSession, user_id: uuid.UUID) -> MeResponse:
    stmt = select(AppUser).where(AppUser.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("Người dùng không tồn tại.")

    roles = await _get_user_roles(db, user.id)
    permissions = await _get_user_permissions(db, user.id)

    return MeResponse(
        user=UserBrief.model_validate(user),
        roles=roles,
        permissions=permissions,
    )
