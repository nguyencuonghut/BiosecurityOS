"""API routers for Killer Metrics module (Sprint 04)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.killer_metrics import schemas, service
from app.shared.exceptions import success_response
from app.shared.optimistic_lock import etag_headers
from app.shared.pagination import PaginationParams, paginated_response

# ── Definition router ──

definition_router = APIRouter()


@definition_router.get("", dependencies=[require_permission("KILLER_EVENT_READ")])
async def list_definitions(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_definitions(db)
    data = [schemas.KillerMetricDefinitionOut.model_validate(d).model_dump(mode="json") for d in items]
    return success_response(request, data)


@definition_router.post("", dependencies=[require_permission("KILLER_EVENT_WRITE")])
async def create_definition(
    request: Request,
    payload: schemas.KillerMetricDefinitionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    defn = await service.create_definition(db, payload)
    data = schemas.KillerMetricDefinitionOut.model_validate(defn).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@definition_router.patch("/{definition_id}", dependencies=[require_permission("KILLER_EVENT_WRITE")])
async def update_definition(
    request: Request,
    definition_id: uuid.UUID,
    payload: schemas.KillerMetricDefinitionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    defn = await service.update_definition(db, definition_id, payload)
    data = schemas.KillerMetricDefinitionOut.model_validate(defn).model_dump(mode="json")
    return success_response(request, data)


# ── Event router ──

event_router = APIRouter()


@event_router.get("", dependencies=[require_permission("KILLER_EVENT_READ")])
async def list_events(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_id: Annotated[uuid.UUID | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    definition_id: Annotated[uuid.UUID | None, Query()] = None,
):
    items, total = await service.list_events(
        db, farm_id=farm_id, status=status, definition_id=definition_id,
        page=pagination.page, page_size=pagination.page_size,
    )
    data = [_event_to_dict(e) for e in items]
    return paginated_response(request, data, total, pagination)


@event_router.get("/{event_id}", dependencies=[require_permission("KILLER_EVENT_READ")])
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event = await service.get_event(db, event_id)
    return success_response(request, _event_to_dict(event), headers=etag_headers(event.version))


@event_router.post("", dependencies=[require_permission("KILLER_EVENT_WRITE")])
async def create_event(
    request: Request,
    payload: schemas.KillerMetricEventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    event = await service.create_event(db, payload, user.id, user.full_name)
    return success_response(request, _event_to_dict(event), status_code=201)


@event_router.patch("/{event_id}", dependencies=[require_permission("KILLER_EVENT_WRITE")])
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    payload: schemas.KillerMetricEventUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event = await service.update_event(db, event_id, payload)
    return success_response(request, _event_to_dict(event), headers=etag_headers(event.version))


# ── Helper ──

def _event_to_dict(event) -> dict:
    out = schemas.KillerMetricEventOut.model_validate(event).model_dump(mode="json")
    if event.definition:
        out["definition"] = schemas.DefinitionBrief.model_validate(event.definition).model_dump(mode="json")
    return out
