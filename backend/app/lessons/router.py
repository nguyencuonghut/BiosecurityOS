"""API router for Lesson Learned module (Sprint 08)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.lessons import schemas, service
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

lesson_router = APIRouter()
lesson_search_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# CRUD (B08.1)
# ═══════════════════════════════════════════════════════════════════

@lesson_router.get("", dependencies=[require_permission("LESSON_READ")])
async def list_lessons(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_type: Annotated[str | None, Query()] = None,
    issue_type: Annotated[str | None, Query()] = None,
    confidence_level: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_lessons(
        db,
        farm_type=farm_type,
        issue_type=issue_type,
        confidence_level=confidence_level,
        status=status,
        tag=tag,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    data = [schemas.LessonListOut.model_validate(l).model_dump(mode="json") for l in items]
    return paginated_response(request, data, total, pagination)


@lesson_router.post("", dependencies=[require_permission("LESSON_WRITE")])
async def create_lesson(
    body: schemas.LessonCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    lesson = await service.create_lesson(db, body)
    return success_response(
        request,
        schemas.LessonOut.model_validate(lesson).model_dump(mode="json"),
        status_code=201,
    )


@lesson_router.get("/{lesson_id}", dependencies=[require_permission("LESSON_READ")])
async def get_lesson(
    lesson_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lesson = await service.get_lesson(db, lesson_id)
    return success_response(
        request,
        schemas.LessonOut.model_validate(lesson).model_dump(mode="json"),
    )


@lesson_router.patch("/{lesson_id}", dependencies=[require_permission("LESSON_WRITE")])
async def update_lesson(
    lesson_id: uuid.UUID,
    body: schemas.LessonUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    lesson = await service.update_lesson(db, lesson_id, body)
    return success_response(
        request,
        schemas.LessonOut.model_validate(lesson).model_dump(mode="json"),
    )


# ═══════════════════════════════════════════════════════════════════
# Validate (B08.2)
# ═══════════════════════════════════════════════════════════════════

@lesson_router.post("/{lesson_id}/validate", dependencies=[require_permission("LESSON_VALIDATE")])
async def validate_lesson(
    lesson_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    lesson = await service.validate_lesson(db, lesson_id, user.id)
    return success_response(
        request,
        schemas.LessonOut.model_validate(lesson).model_dump(mode="json"),
    )


# ═══════════════════════════════════════════════════════════════════
# References (B08.3)
# ═══════════════════════════════════════════════════════════════════

@lesson_router.post("/{lesson_id}/references", dependencies=[require_permission("LESSON_WRITE")])
async def add_reference(
    lesson_id: uuid.UUID,
    body: schemas.ReferenceCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    ref = await service.add_reference(db, lesson_id, body)
    return success_response(
        request,
        schemas.ReferenceOut.model_validate(ref).model_dump(mode="json"),
        status_code=201,
    )


# ═══════════════════════════════════════════════════════════════════
# Tags (B08.4)
# ═══════════════════════════════════════════════════════════════════

@lesson_router.post("/{lesson_id}/tags", dependencies=[require_permission("LESSON_WRITE")])
async def add_tag(
    lesson_id: uuid.UUID,
    body: schemas.TagCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    tag = await service.add_tag(db, lesson_id, body)
    return success_response(
        request,
        schemas.TagOut.model_validate(tag).model_dump(mode="json"),
        status_code=201,
    )


# ═══════════════════════════════════════════════════════════════════
# Similar Search (B08.5)
# ═══════════════════════════════════════════════════════════════════

@lesson_search_router.get("/similar", dependencies=[require_permission("LESSON_READ")])
async def search_similar(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_type: Annotated[str | None, Query()] = None,
    ownership_type: Annotated[str | None, Query()] = None,
    issue_type: Annotated[str | None, Query()] = None,
    area_type: Annotated[str | None, Query()] = None,
    route_type: Annotated[str | None, Query()] = None,
    season: Annotated[str | None, Query()] = None,
):
    items, total = await service.search_similar(
        db,
        farm_type=farm_type,
        ownership_type=ownership_type,
        issue_type=issue_type,
        area_type=area_type,
        route_type=route_type,
        season=season,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    data = [schemas.LessonOut.model_validate(l).model_dump(mode="json") for l in items]
    return paginated_response(request, data, total, pagination)
