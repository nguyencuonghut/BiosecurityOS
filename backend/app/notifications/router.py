"""Notification router (B10.4)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.notifications import service
from app.notifications.schemas import BulkReadRequest, NotificationOut
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


@router.get(
    "",
    dependencies=[require_permission("NOTIFICATION_READ")],
)
async def list_notifications(
    request: Request,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[str | None, Query(description="Filter by status")] = None,
):
    """List current user's notifications."""
    rows, total = await service.list_notifications(
        db,
        recipient_user_id=current_user.id,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items = [NotificationOut.model_validate(r).model_dump(mode="json") for r in rows]
    return paginated_response(request, items, total, pagination)


@router.get(
    "/unread-count",
    dependencies=[require_permission("NOTIFICATION_READ")],
)
async def unread_count(
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get unread notification count for badge."""
    count = await service.get_unread_count(db, recipient_user_id=current_user.id)
    return success_response(request, {"unread_count": count})


@router.post(
    "/{notification_id}/read",
    dependencies=[require_permission("NOTIFICATION_READ")],
)
async def mark_read(
    request: Request,
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a single notification as read."""
    updated = await service.mark_read(db, notification_id=notification_id, user_id=current_user.id)
    return success_response(request, {"updated": updated})


@router.post(
    "/bulk-read",
    dependencies=[require_permission("NOTIFICATION_READ")],
)
async def bulk_read(
    request: Request,
    body: BulkReadRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark multiple notifications as read."""
    count = await service.bulk_mark_read(
        db,
        notification_ids=body.notification_ids,
        user_id=current_user.id,
    )
    return success_response(request, {"updated_count": count})
