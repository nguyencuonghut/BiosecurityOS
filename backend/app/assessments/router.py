"""Assessment API router — CRUD, bulk-upsert, submit, spider chart, attachments (B03.3–B03.8)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments import service
from app.assessments.schemas import (
    AssessmentAttachmentCreate,
    AssessmentAttachmentOut,
    AssessmentCreate,
    AssessmentDetailOut,
    AssessmentItemResultOut,
    AssessmentOut,
    AssessmentUpdate,
    BulkUpsertRequest,
    SpiderChartOut,
)
from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


# ── Assessment CRUD ─────────────────────────────────────────────

@router.get("")
async def list_assessments(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: CurrentUser,
    _perm: Annotated[None, require_permission("ASSESSMENT_READ")],
    farm_id: Annotated[str | None, Query()] = None,
    assessment_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    date_from: Annotated[str | None, Query()] = None,
    date_to: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_assessments(
        db,
        farm_id=uuid.UUID(farm_id) if farm_id else None,
        assessment_type=assessment_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items_out = [AssessmentOut.model_validate(a).model_dump(mode="json") for a in items]
    return paginated_response(request, items_out, total, pagination)


@router.post("", status_code=201)
async def create_assessment(
    request: Request,
    body: AssessmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    obj = await service.create_assessment(db, body, current_user)
    data = AssessmentOut.model_validate(obj).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.get("/{assessment_id}")
async def get_assessment(
    request: Request,
    assessment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_READ")],
):
    obj = await service.get_assessment(db, uuid.UUID(assessment_id))
    data = AssessmentDetailOut.model_validate(obj).model_dump(mode="json")
    return success_response(request, data)


@router.patch("/{assessment_id}")
async def update_assessment(
    request: Request,
    assessment_id: str,
    body: AssessmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    obj = await service.update_assessment(db, uuid.UUID(assessment_id), body)
    data = AssessmentOut.model_validate(obj).model_dump(mode="json")
    return success_response(request, data)


# ── Bulk Upsert Item Results (B03.4) ───────────────────────────

@router.post("/{assessment_id}/items/bulk-upsert")
async def bulk_upsert_items(
    request: Request,
    assessment_id: str,
    body: BulkUpsertRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    results = await service.bulk_upsert_item_results(db, uuid.UUID(assessment_id), body)
    data = [AssessmentItemResultOut.model_validate(r).model_dump(mode="json") for r in results]
    return success_response(request, data)


# ── Submit Assessment (B03.5) ──────────────────────────────────

@router.post("/{assessment_id}/submit")
async def submit_assessment(
    request: Request,
    assessment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    obj = await service.submit_assessment(db, uuid.UUID(assessment_id))
    data = AssessmentOut.model_validate(obj).model_dump(mode="json")
    return success_response(request, data)


# ── Spider Chart (B03.7) ──────────────────────────────────────

@router.get("/{assessment_id}/spider-chart")
async def get_spider_chart(
    request: Request,
    assessment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_READ")],
):
    data = await service.get_spider_chart(db, uuid.UUID(assessment_id))
    return success_response(request, data)


# ── Attachments ────────────────────────────────────────────────

@router.post("/{assessment_id}/attachments", status_code=201)
async def add_attachment(
    request: Request,
    assessment_id: str,
    body: AssessmentAttachmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    att = await service.add_attachment(db, uuid.UUID(assessment_id), body)
    data = AssessmentAttachmentOut.model_validate(att).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ── Change Status (B03.8 — state machine) ─────────────────────

@router.post("/{assessment_id}/change-status")
async def change_status(
    request: Request,
    assessment_id: str,
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("ASSESSMENT_WRITE")],
):
    target = body.get("status")
    version = body.get("version")
    if not target or version is None:
        from app.shared.exceptions import ValidationException
        raise ValidationException("Phải cung cấp 'status' và 'version'.")
    obj = await service.change_status(db, uuid.UUID(assessment_id), target, version)
    data = AssessmentOut.model_validate(obj).model_dump(mode="json")
    return success_response(request, data)
