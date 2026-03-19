"""Audit log admin router (B10.7)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.audit_logs import service
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


@router.get(
    "",
    dependencies=[require_permission("AUDIT_LOG_READ")],
)
async def list_audit_logs(
    request: Request,
    _current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: Annotated[str | None, Query(description="Filter by entity type")] = None,
    entity_id: Annotated[uuid.UUID | None, Query(description="Filter by entity ID")] = None,
    actor_user_id: Annotated[uuid.UUID | None, Query(description="Filter by actor user ID")] = None,
    action: Annotated[str | None, Query(description="Filter by action (partial match)")] = None,
    date_from: Annotated[date | None, Query(description="From date (inclusive)")] = None,
    date_to: Annotated[date | None, Query(description="To date (inclusive)")] = None,
):
    """List audit log entries with filters. Admin only."""
    items, total = await service.list_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return paginated_response(request, items, total, pagination)
