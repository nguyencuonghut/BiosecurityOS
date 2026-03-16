"""Scorecard API router — Template, Section, Item CRUD + activate/archive (B03.1, B03.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.scorecards import service
from app.scorecards.schemas import (
    ScorecardItemCreate,
    ScorecardItemOut,
    ScorecardItemUpdate,
    ScorecardSectionCreate,
    ScorecardSectionDetailOut,
    ScorecardSectionOut,
    ScorecardSectionUpdate,
    ScorecardTemplateCreate,
    ScorecardTemplateDetailOut,
    ScorecardTemplateOut,
    ScorecardTemplateUpdate,
)
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


# ── Template CRUD ───────────────────────────────────────────────

@router.get("")
async def list_templates(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: CurrentUser,
    _perm: Annotated[None, require_permission("SCORECARD_READ")],
    farm_type: Annotated[str | None, Query()] = None,
    ownership_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_templates(
        db,
        farm_type=farm_type,
        ownership_type=ownership_type,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items_out = [ScorecardTemplateOut.model_validate(t).model_dump(mode="json") for t in items]
    return paginated_response(request, items_out, total, pagination)


@router.post("", status_code=201)
async def create_template(
    request: Request,
    body: ScorecardTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    tmpl = await service.create_template(db, body)
    data = ScorecardTemplateOut.model_validate(tmpl).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.get("/{template_id}")
async def get_template(
    request: Request,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_READ")],
):
    tmpl = await service.get_template_detail(db, uuid.UUID(template_id))
    data = ScorecardTemplateDetailOut.model_validate(tmpl).model_dump(mode="json")
    return success_response(request, data)


@router.patch("/{template_id}")
async def update_template(
    request: Request,
    template_id: str,
    body: ScorecardTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    tmpl = await service.update_template(db, uuid.UUID(template_id), body)
    data = ScorecardTemplateOut.model_validate(tmpl).model_dump(mode="json")
    return success_response(request, data)


@router.post("/{template_id}/activate")
async def activate_template(
    request: Request,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    tmpl = await service.activate_template(db, uuid.UUID(template_id))
    data = ScorecardTemplateOut.model_validate(tmpl).model_dump(mode="json")
    return success_response(request, data)


@router.post("/{template_id}/archive")
async def archive_template(
    request: Request,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    tmpl = await service.archive_template(db, uuid.UUID(template_id))
    data = ScorecardTemplateOut.model_validate(tmpl).model_dump(mode="json")
    return success_response(request, data)


# ── Section CRUD ────────────────────────────────────────────────

@router.get("/{template_id}/sections")
async def list_sections(
    request: Request,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_READ")],
):
    items = await service.list_sections(db, uuid.UUID(template_id))
    data = [ScorecardSectionDetailOut.model_validate(s).model_dump(mode="json") for s in items]
    return success_response(request, data)


@router.post("/{template_id}/sections", status_code=201)
async def create_section(
    request: Request,
    template_id: str,
    body: ScorecardSectionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    section = await service.create_section(db, uuid.UUID(template_id), body)
    data = ScorecardSectionOut.model_validate(section).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ── Section (by section_id — flat URL per API contract) ─────────

section_router = APIRouter()


@section_router.patch("/{section_id}")
async def update_section(
    request: Request,
    section_id: str,
    body: ScorecardSectionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    section = await service.update_section(db, uuid.UUID(section_id), body)
    data = ScorecardSectionOut.model_validate(section).model_dump(mode="json")
    return success_response(request, data)


@section_router.get("/{section_id}/items")
async def list_items(
    request: Request,
    section_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_READ")],
):
    items = await service.list_items(db, uuid.UUID(section_id))
    data = [ScorecardItemOut.model_validate(i).model_dump(mode="json") for i in items]
    return success_response(request, data)


@section_router.post("/{section_id}/items", status_code=201)
async def create_item(
    request: Request,
    section_id: str,
    body: ScorecardItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    item = await service.create_item(db, uuid.UUID(section_id), body)
    data = ScorecardItemOut.model_validate(item).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ── Item (by item_id — flat URL per API contract) ───────────────

item_router = APIRouter()


@item_router.patch("/{item_id}")
async def update_item(
    request: Request,
    item_id: str,
    body: ScorecardItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    item = await service.update_item(db, uuid.UUID(item_id), body)
    data = ScorecardItemOut.model_validate(item).model_dump(mode="json")
    return success_response(request, data)


@item_router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _perm: Annotated[None, require_permission("SCORECARD_WRITE")],
):
    await service.delete_item(db, uuid.UUID(item_id))
