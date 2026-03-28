"""Farm API router — CRUD farm, area, route, external risk point (B02.3–B02.6)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.farms import service
from app.farms.schemas import (
    AreaCreate,
    AreaOut,
    AreaTypeCreate,
    AreaTypeOut,
    AreaTypeUpdate,
    AreaUpdate,
    ExternalRiskPointCreate,
    ExternalRiskPointOut,
    FarmCreate,
    FarmOut,
    FarmUpdate,
    RouteCreate,
    RouteOut,
)
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


# ── Area Types (reference data) ─────────────────────────────────

@router.get("/area-types")
async def list_area_types(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    items = await service.list_area_types(db)
    data = [AreaTypeOut.model_validate(t).model_dump(mode="json") for t in items]
    return success_response(request, data)


@router.post("/area-types", status_code=201)
async def create_area_type(
    request: Request,
    body: AreaTypeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    obj = await service.create_area_type(db, body)
    await db.commit()
    return success_response(request, AreaTypeOut.model_validate(obj).model_dump(mode="json"))


@router.put("/area-types/{area_type_id}")
async def update_area_type(
    area_type_id: uuid.UUID,
    request: Request,
    body: AreaTypeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    obj = await service.update_area_type(db, area_type_id, body)
    await db.commit()
    return success_response(request, AreaTypeOut.model_validate(obj).model_dump(mode="json"))


@router.delete("/area-types/{area_type_id}", status_code=204)
async def delete_area_type(
    area_type_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    await service.delete_area_type(db, area_type_id)
    await db.commit()


# ── Farm CRUD ───────────────────────────────────────────────────

@router.get("")
async def list_farms(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    _: Annotated[None, require_permission("FARM_READ")],
    region_id: Annotated[str | None, Query()] = None,
    farm_type: Annotated[str | None, Query()] = None,
    ownership_type: Annotated[str | None, Query()] = None,
    operational_status: Annotated[str | None, Query()] = None,
    baseline_risk_level: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_farms(
        db,
        current_user,
        region_id=uuid.UUID(region_id) if region_id else None,
        farm_type=farm_type,
        ownership_type=ownership_type,
        operational_status=operational_status,
        baseline_risk_level=baseline_risk_level,
        search=search,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items_out = [FarmOut.model_validate(f).model_dump(mode="json") for f in items]
    return paginated_response(request, items_out, total, pagination)


@router.post("", status_code=201)
async def create_farm(
    request: Request,
    body: FarmCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    farm = await service.create_farm(db, body)
    data = FarmOut.model_validate(farm).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.get("/{farm_id}")
async def get_farm(
    request: Request,
    farm_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    farm = await service.get_farm(db, uuid.UUID(farm_id))
    data = FarmOut.model_validate(farm).model_dump(mode="json")
    return success_response(request, data)


@router.patch("/{farm_id}")
async def update_farm(
    request: Request,
    farm_id: str,
    body: FarmUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    farm = await service.update_farm(db, uuid.UUID(farm_id), body)
    data = FarmOut.model_validate(farm).model_dump(mode="json")
    return success_response(request, data)


# ── Farm Area ───────────────────────────────────────────────────

@router.get("/{farm_id}/areas")
async def list_areas(
    request: Request,
    farm_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    items = await service.list_areas(db, uuid.UUID(farm_id))
    data = [AreaOut.model_validate(a).model_dump(mode="json") for a in items]
    return success_response(request, data)


@router.post("/{farm_id}/areas", status_code=201)
async def create_area(
    request: Request,
    farm_id: str,
    body: AreaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    area = await service.create_area(db, uuid.UUID(farm_id), body)
    data = AreaOut.model_validate(area).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.patch("/{farm_id}/areas/{area_id}")
async def update_area(
    request: Request,
    farm_id: str,
    area_id: str,
    body: AreaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    area = await service.update_area(db, uuid.UUID(farm_id), uuid.UUID(area_id), body)
    data = AreaOut.model_validate(area).model_dump(mode="json")
    return success_response(request, data)


# ── Farm Route ──────────────────────────────────────────────────

@router.get("/{farm_id}/routes")
async def list_routes(
    request: Request,
    farm_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    items = await service.list_routes(db, uuid.UUID(farm_id))
    data = [RouteOut.model_validate(r).model_dump(mode="json") for r in items]
    return success_response(request, data)


@router.post("/{farm_id}/routes", status_code=201)
async def create_route(
    request: Request,
    farm_id: str,
    body: RouteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    route = await service.create_route(db, uuid.UUID(farm_id), body)
    data = RouteOut.model_validate(route).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ── External Risk Point ─────────────────────────────────────────

@router.get("/{farm_id}/external-risk-points")
async def list_risk_points(
    request: Request,
    farm_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    items = await service.list_risk_points(db, uuid.UUID(farm_id))
    data = [ExternalRiskPointOut.model_validate(r).model_dump(mode="json") for r in items]
    return success_response(request, data)


@router.post("/{farm_id}/external-risk-points", status_code=201)
async def create_risk_point(
    request: Request,
    farm_id: str,
    body: ExternalRiskPointCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_WRITE")],
):
    rp = await service.create_risk_point(db, uuid.UUID(farm_id), body)
    data = ExternalRiskPointOut.model_validate(rp).model_dump(mode="json")
    return success_response(request, data, status_code=201)
