"""User API router — CRUD users + role assignment + permission management (B02.1, B02.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response
from app.users import service
from app.users.schemas import UserCreate, UserOut, UserRoleAssign, UserRoleOut, UserUpdate

router = APIRouter()


def _user_to_dict(user) -> dict:
    """Convert AppUser ORM with loaded roles to UserOut dict."""
    roles = []
    for ur in user.user_roles:
        roles.append(UserRoleOut(
            id=ur.id,
            role_id=ur.role_id,
            role_code=ur.role.code if ur.role else None,
            role_name=ur.role.name if ur.role else None,
            scope_region_id=ur.scope_region_id,
            scope_farm_id=ur.scope_farm_id,
            effective_from=ur.effective_from,
            effective_to=ur.effective_to,
        ).model_dump(mode="json"))

    out = UserOut.model_validate(user).model_dump(mode="json")
    out["roles"] = roles
    return out


@router.get("/roles")
async def list_roles(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    """Return all available roles for the role assignment UI."""
    roles = await service.list_roles(db)
    data = [{"id": str(r.id), "code": r.code, "name": r.name, "scope_type": r.scope_type} for r in roles]
    return success_response(request, data)


@router.get("")
async def list_users(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
    status: Annotated[str | None, Query()] = None,
    region_id: Annotated[str | None, Query()] = None,
    farm_id: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_users(
        db,
        status=status,
        region_id=uuid.UUID(region_id) if region_id else None,
        farm_id=uuid.UUID(farm_id) if farm_id else None,
        role=role,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items_out = [_user_to_dict(u) for u in items]
    return paginated_response(request, items_out, total, pagination)


@router.post("", status_code=201)
async def create_user(
    request: Request,
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    user = await service.create_user(db, body)
    return success_response(request, _user_to_dict(user), status_code=201)


# ── Permission management endpoints (must be before /{user_id}) ──

@router.get("/permissions")
async def list_permissions(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    """Return all system permissions grouped by module."""
    perms = await service.list_permissions(db)
    data = [
        {
            "id": str(p.id),
            "code": p.code,
            "name": p.name,
            "module": p.module,
            "action": p.action,
        }
        for p in perms
    ]
    return success_response(request, data)


@router.get("/roles/{role_id}")
async def get_role(
    request: Request,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    """Return a role with its full permission list."""
    role = await service.get_role(db, uuid.UUID(role_id))
    perm_ids = [str(rp.permission_id) for rp in role.role_permissions]
    data = {
        "id": str(role.id),
        "code": role.code,
        "name": role.name,
        "scope_type": role.scope_type,
        "description": role.description,
        "permission_ids": perm_ids,
    }
    return success_response(request, data)


@router.post("/roles/{role_id}/permissions/{permission_id}", status_code=201)
async def assign_permission(
    request: Request,
    role_id: str,
    permission_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    """Grant a permission to a role."""
    await service.assign_permission_to_role(db, uuid.UUID(role_id), uuid.UUID(permission_id))
    return success_response(request, {"role_id": role_id, "permission_id": permission_id}, status_code=201)


@router.delete("/roles/{role_id}/permissions/{permission_id}", status_code=204)
async def revoke_permission(
    role_id: str,
    permission_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    """Revoke a permission from a role."""
    await service.remove_permission_from_role(db, uuid.UUID(role_id), uuid.UUID(permission_id))


# ── User CRUD ────────────────────────────────────────────────────

@router.get("/{user_id}")
async def get_user(
    request: Request,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    user = await service.get_user(db, uuid.UUID(user_id))
    return success_response(request, _user_to_dict(user))


@router.patch("/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    body: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    user = await service.update_user(db, uuid.UUID(user_id), body)
    return success_response(request, _user_to_dict(user))


@router.post("/{user_id}/roles", status_code=201)
async def assign_role(
    request: Request,
    user_id: str,
    body: UserRoleAssign,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    ur = await service.assign_role(db, uuid.UUID(user_id), body)
    data = UserRoleOut.model_validate(ur).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.delete("/{user_id}/roles/{user_role_id}", status_code=204)
async def remove_role(
    user_id: str,
    user_role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    await service.remove_role(db, uuid.UUID(user_id), uuid.UUID(user_role_id))

