"""API routers for Floorplan / Digital Twin module (Sprint 07)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.floorplans import schemas, service
from app.shared.exceptions import success_response

# ═══════════════════════════════════════════════════════════════════
# Floorplan Version router (nested under /farms/{farm_id}/floorplans)
# ═══════════════════════════════════════════════════════════════════

farm_floorplan_router = APIRouter()


@farm_floorplan_router.get(
    "/{farm_id}/floorplans", dependencies=[require_permission("SCAR_READ")]
)
async def list_floorplans(
    farm_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_floorplans(db, farm_id)
    return success_response(
        request,
        [schemas.FloorplanVersionOut.model_validate(fp).model_dump(mode="json") for fp in items]
    )


@farm_floorplan_router.post(
    "/{farm_id}/floorplans", dependencies=[require_permission("SCAR_WRITE")]
)
async def create_floorplan(
    farm_id: uuid.UUID,
    body: schemas.FloorplanVersionCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    fp = await service.create_floorplan(db, farm_id, body)
    return success_response(
        request,
        schemas.FloorplanVersionOut.model_validate(fp).model_dump(mode="json"), status_code=201
    )


# ═══════════════════════════════════════════════════════════════════
# Floorplan direct router (/floorplans/{floorplan_id})
# ═══════════════════════════════════════════════════════════════════

floorplan_router = APIRouter()


@floorplan_router.get(
    "/{floorplan_id}", dependencies=[require_permission("SCAR_READ")]
)
async def get_floorplan(
    floorplan_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    fp = await service.get_floorplan(db, floorplan_id)
    return success_response(
        request,
        schemas.FloorplanVersionOut.model_validate(fp).model_dump(mode="json")
    )


@floorplan_router.patch(
    "/{floorplan_id}", dependencies=[require_permission("SCAR_WRITE")]
)
async def update_floorplan(
    floorplan_id: uuid.UUID,
    body: schemas.FloorplanVersionUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    fp = await service.update_floorplan(db, floorplan_id, body)
    return success_response(
        request,
        schemas.FloorplanVersionOut.model_validate(fp).model_dump(mode="json")
    )


@floorplan_router.post(
    "/{floorplan_id}/approve", dependencies=[require_permission("SCAR_WRITE")]
)
async def approve_floorplan(
    floorplan_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    fp = await service.approve_floorplan(db, floorplan_id, user.id)
    return success_response(
        request,
        schemas.FloorplanVersionOut.model_validate(fp).model_dump(mode="json")
    )


# ── Marker sub-routes ──

@floorplan_router.get(
    "/{floorplan_id}/markers", dependencies=[require_permission("SCAR_READ")]
)
async def list_markers(
    floorplan_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_markers(db, floorplan_id)
    return success_response(
        request,
        [schemas.MarkerOut.model_validate(m).model_dump(mode="json") for m in items]
    )


@floorplan_router.post(
    "/{floorplan_id}/markers", dependencies=[require_permission("SCAR_WRITE")]
)
async def create_marker(
    floorplan_id: uuid.UUID,
    body: schemas.MarkerCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    marker = await service.create_marker(db, floorplan_id, body)
    return success_response(
        request,
        schemas.MarkerOut.model_validate(marker).model_dump(mode="json"), status_code=201
    )


@floorplan_router.patch(
    "/{floorplan_id}/markers/{marker_id}", dependencies=[require_permission("SCAR_WRITE")]
)
async def update_marker(
    floorplan_id: uuid.UUID,
    marker_id: uuid.UUID,
    body: schemas.MarkerUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    marker = await service.update_marker(db, marker_id, body)
    return success_response(
        request,
        schemas.MarkerOut.model_validate(marker).model_dump(mode="json")
    )


@floorplan_router.delete(
    "/{floorplan_id}/markers/{marker_id}", dependencies=[require_permission("SCAR_WRITE")]
)
async def delete_marker(
    floorplan_id: uuid.UUID,
    marker_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await service.delete_marker(db, marker_id)
    return success_response(request, None, status_code=204)
