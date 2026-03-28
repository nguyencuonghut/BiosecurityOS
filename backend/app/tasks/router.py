"""API routers for Corrective Task module (Sprint 06)."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.shared.exceptions import success_response
from app.shared.optimistic_lock import etag_headers
from app.shared.pagination import PaginationParams, paginated_response
from app.tasks import schemas, service
from app.tasks.models import TaskStatus, TaskType


# ═══════════════════════════════════════════════════════════════════
# Task router
# ═══════════════════════════════════════════════════════════════════

task_router = APIRouter()


@task_router.get("", dependencies=[require_permission("TASK_READ")])
async def list_tasks(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
    farm_id: Annotated[uuid.UUID | None, Query()] = None,
    case_id: Annotated[uuid.UUID | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    task_type: Annotated[TaskType | None, Query()] = None,
    assignee_user_id: Annotated[uuid.UUID | None, Query()] = None,
    overdue: Annotated[bool, Query()] = False,
):
    items, total = await service.list_tasks(
        db,
        farm_id=farm_id,
        case_id=case_id,
        priority=priority,
        status=status,
        task_type=task_type,
        assignee_user_id=assignee_user_id,
        overdue=overdue,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    data = [schemas.TaskListOut.model_validate(t).model_dump(mode="json") for t in items]
    return paginated_response(request, data, total, pagination)


@task_router.post("", dependencies=[require_permission("TASK_CREATE")])
async def create_task(
    request: Request,
    payload: schemas.TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    task = await service.create_task(db, payload, user.id)
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@task_router.get("/{task_id}", dependencies=[require_permission("TASK_READ")])
async def get_task(
    request: Request,
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await service.get_task(db, task_id)
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, headers=etag_headers(task.version))


@task_router.patch("/{task_id}", dependencies=[require_permission("TASK_CREATE")])
async def update_task(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await service.update_task(db, task_id, payload)
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, headers=etag_headers(task.version))


@task_router.post("/{task_id}/change-status", dependencies=[require_permission("TASK_CREATE")])
async def change_status(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.ChangeTaskStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    task = await service.change_status(db, task_id, payload, user.id)
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, headers=etag_headers(task.version))


# ── Submit for review (B06.4) ──

class SubmitForReviewRequest(BaseModel):
    version: int


@task_router.post("/{task_id}/submit-for-review", dependencies=[require_permission("TASK_CREATE")])
async def submit_for_review(
    request: Request,
    task_id: uuid.UUID,
    payload: SubmitForReviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await service.submit_for_review(db, task_id, payload.version)
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, headers=etag_headers(task.version))


# ── Close task (B06.5) ──

class CloseTaskRequest(BaseModel):
    version: int


@task_router.post("/{task_id}/close", dependencies=[require_permission("TASK_CREATE")])
async def close_task(
    request: Request,
    task_id: uuid.UUID,
    payload: CloseTaskRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    task = await service.change_status(
        db, task_id,
        schemas.ChangeTaskStatusRequest(target_status="closed", version=payload.version),
        user.id,
    )
    data = schemas.TaskOut.model_validate(task).model_dump(mode="json")
    return success_response(request, data, headers=etag_headers(task.version))


# ═══════════════════════════════════════════════════════════════════
# Assignees (B06.3)
# ═══════════════════════════════════════════════════════════════════

@task_router.post("/{task_id}/assignees", dependencies=[require_permission("TASK_CREATE")])
async def add_assignee(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.TaskAssigneeInput,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    assignee = await service.add_assignee(db, task_id, payload)
    data = schemas.TaskAssigneeOut.model_validate(assignee).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@task_router.delete("/{task_id}/assignees/{assignee_id}", dependencies=[require_permission("TASK_CREATE")])
async def remove_assignee(
    request: Request,
    task_id: uuid.UUID,
    assignee_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await service.remove_assignee(db, task_id, assignee_id)
    return success_response(request, None)


# ═══════════════════════════════════════════════════════════════════
# Task Attachments (link attachment to task)
# ═══════════════════════════════════════════════════════════════════

@task_router.get("/{task_id}/attachments", dependencies=[require_permission("TASK_READ")])
async def list_task_attachments(
    request: Request,
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_task_attachments(db, task_id)
    data = [schemas.TaskAttachmentDetailOut.model_validate(a).model_dump(mode="json") for a in items]
    return success_response(request, data)


@task_router.post("/{task_id}/attachments", dependencies=[require_permission("TASK_CREATE")])
async def add_task_attachment(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.TaskAttachmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    link = await service.add_task_attachment(db, task_id, payload)
    data = schemas.TaskAttachmentOut.model_validate(link).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ═══════════════════════════════════════════════════════════════════
# Reviews (B06.5)
# ═══════════════════════════════════════════════════════════════════

@task_router.get("/{task_id}/reviews", dependencies=[require_permission("TASK_READ")])
async def list_reviews(
    request: Request,
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_reviews(db, task_id)
    data = [schemas.TaskReviewOut.model_validate(r).model_dump(mode="json") for r in items]
    return success_response(request, data)


@task_router.post("/{task_id}/reviews", dependencies=[require_permission("TASK_REVIEW")])
async def create_review(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.TaskReviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    review = await service.create_review(db, task_id, payload, user.id)
    data = schemas.TaskReviewOut.model_validate(review).model_dump(mode="json")
    return success_response(request, data, status_code=201)


class ReviewNoteRequest(BaseModel):
    review_note: str | None = None


@task_router.post("/{task_id}/approve", dependencies=[require_permission("TASK_REVIEW")])
async def approve_task(
    request: Request,
    task_id: uuid.UUID,
    payload: ReviewNoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    review = await service.approve_task(db, task_id, user.id, payload.review_note)
    data = schemas.TaskReviewOut.model_validate(review).model_dump(mode="json")
    return success_response(request, data, status_code=201)


class RejectRequest(BaseModel):
    review_note: str
    next_action_due_at: datetime | None = None


@task_router.post("/{task_id}/reject", dependencies=[require_permission("TASK_REVIEW")])
async def reject_task(
    request: Request,
    task_id: uuid.UUID,
    payload: RejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    review = await service.reject_task(db, task_id, user.id, payload.review_note, payload.next_action_due_at)
    data = schemas.TaskReviewOut.model_validate(review).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@task_router.post("/{task_id}/request-rework", dependencies=[require_permission("TASK_REVIEW")])
async def request_rework(
    request: Request,
    task_id: uuid.UUID,
    payload: RejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    review = await service.reject_task(db, task_id, user.id, payload.review_note, payload.next_action_due_at)
    data = schemas.TaskReviewOut.model_validate(review).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ═══════════════════════════════════════════════════════════════════
# Comments (B06.6)
# ═══════════════════════════════════════════════════════════════════

@task_router.get("/{task_id}/comments", dependencies=[require_permission("TASK_READ")])
async def list_comments(
    request: Request,
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_comments(db, task_id)
    data = [schemas.TaskCommentOut.model_validate(c).model_dump(mode="json") for c in items]
    return success_response(request, data)


@task_router.post("/{task_id}/comments", dependencies=[require_permission("TASK_READ")])
async def create_comment(
    request: Request,
    task_id: uuid.UUID,
    payload: schemas.TaskCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    comment = await service.create_comment(db, task_id, payload, user.id)
    data = schemas.TaskCommentOut.model_validate(comment).model_dump(mode="json")
    return success_response(request, data, status_code=201)
