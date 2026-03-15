"""Auth dependencies — get_current_user, require_permission (B01.6 RBAC)."""

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AppUser
from app.auth.security import decode_access_token
from app.database import get_db
from app.shared.exceptions import ForbiddenException, UnauthorizedException


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppUser:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedException("Thiếu token xác thực.")

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Token không hợp lệ hoặc đã hết hạn.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token không hợp lệ.")

    stmt = select(AppUser).where(AppUser.id == uuid.UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise UnauthorizedException("Tài khoản không hoạt động.")

    # Attach permissions from token payload to request state for use in require_permission
    request.state.permissions = payload.get("permissions", [])
    return user


CurrentUser = Annotated[AppUser, Depends(get_current_user)]


def require_permission(*required_codes: str):
    """Dependency factory: raises 403 if user lacks any of the required permissions."""

    async def _check(request: Request, _user: CurrentUser):
        user_perms = set(getattr(request.state, "permissions", []))
        missing = set(required_codes) - user_perms
        if missing:
            raise ForbiddenException(f"Thiếu quyền: {', '.join(sorted(missing))}")

    return Depends(_check)
