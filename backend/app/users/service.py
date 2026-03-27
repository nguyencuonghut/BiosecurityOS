"""User service — CRUD + role assignment + permission management."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import AppPermission, AppRole, AppUser, AppUserCredential, RolePermission, UserRole
from app.auth.security import hash_password
from app.shared.exceptions import ConflictException, NotFoundException, ValidationException
from app.users.schemas import UserCreate, UserRoleAssign, UserUpdate


# ── Role queries ────────────────────────────────────────────────

async def list_roles(db: AsyncSession) -> list[AppRole]:
    """Return all roles with their permissions eagerly loaded."""
    result = await db.execute(
        select(AppRole)
        .options(selectinload(AppRole.role_permissions).selectinload(RolePermission.permission))
        .order_by(AppRole.code)
    )
    return list(result.scalars().all())


async def get_role(db: AsyncSession, role_id: uuid.UUID) -> AppRole:
    result = await db.execute(
        select(AppRole)
        .options(selectinload(AppRole.role_permissions).selectinload(RolePermission.permission))
        .where(AppRole.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundException(f"Role {role_id} không tồn tại.")
    return role


# ── Permission queries ──────────────────────────────────────────

async def list_permissions(db: AsyncSession) -> list[AppPermission]:
    """Return all permissions ordered by module then code."""
    result = await db.execute(
        select(AppPermission).order_by(AppPermission.module, AppPermission.code)
    )
    return list(result.scalars().all())


# ── Role-Permission assignment ──────────────────────────────────

async def assign_permission_to_role(
    db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID
) -> RolePermission:
    """Grant a permission to a role. Idempotent — returns existing if already granted."""
    role = await get_role(db, role_id)

    perm_result = await db.execute(
        select(AppPermission).where(AppPermission.id == permission_id)
    )
    permission = perm_result.scalar_one_or_none()
    if not permission:
        raise NotFoundException(f"Permission {permission_id} không tồn tại.")

    existing = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    rp = existing.scalar_one_or_none()
    if rp:
        return rp  # Already granted — idempotent

    rp = RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(rp)
    await db.flush()
    return rp


async def remove_permission_from_role(
    db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID
) -> None:
    """Revoke a permission from a role."""
    await get_role(db, role_id)
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    rp = result.scalar_one_or_none()
    if not rp:
        raise NotFoundException("Permission chưa được gán cho role này.")
    await db.delete(rp)
    await db.flush()


async def list_users(
    db: AsyncSession,
    *,
    status: str | None = None,
    region_id: uuid.UUID | None = None,
    farm_id: uuid.UUID | None = None,
    role: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AppUser], int]:
    query = select(AppUser).options(selectinload(AppUser.user_roles).selectinload(UserRole.role))
    count_query = select(func.count()).select_from(AppUser)

    if status:
        query = query.where(AppUser.status == status)
        count_query = count_query.where(AppUser.status == status)
    if region_id:
        query = query.where(AppUser.region_id == region_id)
        count_query = count_query.where(AppUser.region_id == region_id)
    if farm_id:
        query = query.where(AppUser.farm_id == farm_id)
        count_query = count_query.where(AppUser.farm_id == farm_id)
    if role:
        query = query.join(AppUser.user_roles).join(UserRole.role).where(AppRole.code == role)
        count_query = (
            count_query.join(AppUser.user_roles).join(UserRole.role).where(AppRole.code == role)
        )

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AppUser.username).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().unique().all()), total


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> AppUser:
    result = await db.execute(
        select(AppUser)
        .options(selectinload(AppUser.user_roles).selectinload(UserRole.role))
        .where(AppUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException(f"User {user_id} không tồn tại.")
    return user


async def create_user(db: AsyncSession, data: UserCreate) -> AppUser:
    # Check duplicate username
    existing = await db.execute(select(AppUser).where(AppUser.username == data.username))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Username '{data.username}' đã tồn tại.")

    user_data = data.model_dump(exclude={"password"})
    user = AppUser(**user_data)
    db.add(user)
    await db.flush()

    credential = AppUserCredential(
        user_id=user.id,
        password_hash=hash_password(data.password),
    )
    db.add(credential)
    await db.flush()

    # Reload with roles
    return await get_user(db, user.id)


async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> AppUser:
    user = await get_user(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    # Reload to get fresh data
    return await get_user(db, user_id)


async def assign_role(db: AsyncSession, user_id: uuid.UUID, data: UserRoleAssign) -> UserRole:
    # Verify user exists
    await get_user(db, user_id)

    # Verify role exists
    role_result = await db.execute(select(AppRole).where(AppRole.id == data.role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        raise NotFoundException(f"Role {data.role_id} không tồn tại.")

    # Check for duplicate assignment (same user + same role + same scope)
    dup_query = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == data.role_id,
    )
    if data.scope_region_id:
        dup_query = dup_query.where(UserRole.scope_region_id == data.scope_region_id)
    if data.scope_farm_id:
        dup_query = dup_query.where(UserRole.scope_farm_id == data.scope_farm_id)
    existing = (await db.execute(dup_query)).scalar_one_or_none()
    if existing:
        raise ConflictException("User đã được gán role này với cùng scope.")

    # Validate effective dates
    if data.effective_from and data.effective_to and data.effective_to < data.effective_from:
        raise ValidationException("effective_to phải >= effective_from.")

    user_role = UserRole(user_id=user_id, **data.model_dump())
    db.add(user_role)
    await db.flush()

    # Reload with role relationship
    result = await db.execute(
        select(UserRole).options(selectinload(UserRole.role)).where(UserRole.id == user_role.id)
    )
    return result.scalar_one()


async def remove_role(db: AsyncSession, user_id: uuid.UUID, user_role_id: uuid.UUID) -> None:
    result = await db.execute(
        select(UserRole).where(UserRole.id == user_role_id, UserRole.user_id == user_id)
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        raise NotFoundException(f"UserRole {user_role_id} không tồn tại cho user {user_id}.")
    await db.delete(user_role)
    await db.flush()
