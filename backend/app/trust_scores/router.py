"""API router for Trust Score module (Sprint 04)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_permission
from app.database import get_db
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response
from app.trust_scores import schemas, service

router = APIRouter()


@router.get("", dependencies=[require_permission("TRUST_SCORE_READ")])
async def list_trust_scores(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_id: Annotated[uuid.UUID | None, Query()] = None,
):
    items, total = await service.list_snapshots(db, farm_id=farm_id, page=pagination.page, page_size=pagination.page_size)
    data = [schemas.TrustScoreOut.model_validate(s).model_dump(mode="json") for s in items]
    return paginated_response(request, data, total, pagination)


@router.post("/calculate", dependencies=[require_permission("TRUST_SCORE_WRITE")])
async def calculate_trust_score(
    request: Request,
    payload: schemas.TrustScoreCalculateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await service.calculate_trust_score(db, payload)
    return success_response(request, result, status_code=201)


# B04.4 — mounted on farms router, but also accessible here
@router.get("/farms/{farm_id}/latest", dependencies=[require_permission("TRUST_SCORE_READ")])
async def get_latest_trust_score(
    request: Request,
    farm_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await service.get_latest_trust_score(db, farm_id)
    return success_response(request, result)
