"""API routers for Scar Memory module (Sprint 07)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.floorplans.schemas import FloorplanVersionOut, MarkerOut
from app.scars import schemas, service
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

scar_router = APIRouter()


@scar_router.get("", dependencies=[require_permission("SCAR_READ")])
async def list_scars(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_id: Annotated[uuid.UUID | None, Query()] = None,
    scar_type: Annotated[str | None, Query()] = None,
    confidence_level: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    area_id: Annotated[uuid.UUID | None, Query()] = None,
):
    items, total = await service.list_scars(
        db,
        farm_id=farm_id,
        scar_type=scar_type,
        confidence_level=confidence_level,
        status=status,
        area_id=area_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    data = [schemas.ScarListOut.model_validate(s).model_dump(mode="json") for s in items]
    return paginated_response(request, data, total, pagination)


@scar_router.post("", dependencies=[require_permission("SCAR_WRITE")])
async def create_scar(
    body: schemas.ScarCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    scar = await service.create_scar(db, body, user.id)
    return success_response(
        request,
        schemas.ScarOut.model_validate(scar).model_dump(mode="json"), status_code=201
    )


@scar_router.get("/{scar_id}", dependencies=[require_permission("SCAR_READ")])
async def get_scar(
    scar_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    scar = await service.get_scar(db, scar_id)
    return success_response(
        request,
        schemas.ScarOut.model_validate(scar).model_dump(mode="json")
    )


@scar_router.patch("/{scar_id}", dependencies=[require_permission("SCAR_WRITE")])
async def update_scar(
    scar_id: uuid.UUID,
    body: schemas.ScarUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    scar = await service.update_scar(db, scar_id, body)
    return success_response(
        request,
        schemas.ScarOut.model_validate(scar).model_dump(mode="json")
    )


@scar_router.post("/{scar_id}/validate", dependencies=[require_permission("SCAR_WRITE")])
async def validate_scar(
    scar_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    scar = await service.validate_scar(db, scar_id, user.id)
    return success_response(
        request,
        schemas.ScarOut.model_validate(scar).model_dump(mode="json")
    )


@scar_router.post("/{scar_id}/links", dependencies=[require_permission("SCAR_WRITE")])
async def add_scar_link(
    scar_id: uuid.UUID,
    body: schemas.ScarLinkCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    link = await service.add_scar_link(db, scar_id, body)
    return success_response(
        request,
        schemas.ScarLinkOut.model_validate(link).model_dump(mode="json"), status_code=201
    )


# ═══════════════════════════════════════════════════════════════════
# Scar Map (nested under /farms/{farm_id}/scar-map)
# ═══════════════════════════════════════════════════════════════════

scar_map_router = APIRouter()


@scar_map_router.get(
    "/{farm_id}/scar-map", dependencies=[require_permission("SCAR_READ")]
)
async def get_scar_map(
    farm_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    scar_type: Annotated[str | None, Query()] = None,
    confidence_level: Annotated[str | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
):
    result = await service.get_scar_map(
        db, farm_id,
        scar_type=scar_type,
        confidence_level=confidence_level,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(request, {
        "floorplan": FloorplanVersionOut.model_validate(result["floorplan"]).model_dump(mode="json")
        if result["floorplan"] else None,
        "markers": [MarkerOut.model_validate(m).model_dump(mode="json") for m in result["markers"]],
        "scars": [schemas.ScarMapItem.model_validate(s).model_dump(mode="json") for s in result["scars"]],
    })
