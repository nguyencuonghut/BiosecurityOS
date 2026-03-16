"""Region API router — CRUD regions (B02.7)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.regions import service
from app.regions.schemas import RegionCreate, RegionOut, RegionUpdate
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


@router.get("")
async def list_regions(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
    status: Annotated[str | None, Query()] = None,
):
    items, total = await service.list_regions(
        db, status=status, page=pagination.page, page_size=pagination.page_size
    )
    items_out = [RegionOut.model_validate(r).model_dump(mode="json") for r in items]
    return paginated_response(request, items_out, total, pagination)


@router.post("", status_code=201)
async def create_region(
    request: Request,
    body: RegionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    region = await service.create_region(db, body)
    data = RegionOut.model_validate(region).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.get("/{region_id}")
async def get_region(
    request: Request,
    region_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("FARM_READ")],
):
    import uuid

    region = await service.get_region(db, uuid.UUID(region_id))
    data = RegionOut.model_validate(region).model_dump(mode="json")
    return success_response(request, data)


@router.patch("/{region_id}")
async def update_region(
    request: Request,
    region_id: str,
    body: RegionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_permission("USER_ADMIN")],
):
    import uuid

    region = await service.update_region(db, uuid.UUID(region_id), body)
    data = RegionOut.model_validate(region).model_dump(mode="json")
    return success_response(request, data)
