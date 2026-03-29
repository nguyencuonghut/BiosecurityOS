"""API routers for Risk Case & RCA module (Sprint 05)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.cases import schemas, service
from app.database import get_db
from app.shared.exceptions import success_response
from app.shared.optimistic_lock import etag_headers
from app.shared.pagination import PaginationParams, paginated_response


# ═══════════════════════════════════════════════════════════════════
# Case router
# ═══════════════════════════════════════════════════════════════════

case_router = APIRouter()


@case_router.get("", dependencies=[require_permission("CASE_CREATE")])
async def list_cases(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
    farm_id: Annotated[uuid.UUID | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    current_status: Annotated[str | None, Query()] = None,
    case_type: Annotated[str | None, Query()] = None,
    assigned_expert_user_id: Annotated[uuid.UUID | None, Query()] = None,
    queue: Annotated[str | None, Query()] = None,
):
    queue_my = user.id if queue == "my" else None
    items, total = await service.list_cases(
        db,
        farm_id=farm_id,
        priority=priority,
        current_status=current_status,
        case_type=case_type,
        assigned_expert_user_id=assigned_expert_user_id,
        queue_my=queue_my,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    data = [schemas.CaseOut.model_validate(c).model_dump(mode="json") for c in items]
    for c, d in zip(items, data):
        d["assigned_expert_name"] = c.assigned_expert.full_name if c.assigned_expert else None
    return paginated_response(request, data, total, pagination)


@case_router.post("", dependencies=[require_permission("CASE_CREATE")])
async def create_case(
    request: Request,
    payload: schemas.CaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    case = await service.create_case(db, payload, user.id)
    data = schemas.CaseOut.model_validate(case).model_dump(mode="json")
    data["assigned_expert_name"] = case.assigned_expert.full_name if case.assigned_expert else None
    return success_response(request, data, status_code=201)


@case_router.get("/queue/review", dependencies=[require_permission("CASE_CREATE")])
async def queue_review(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items, total = await service.get_queue_review(
        db, page=pagination.page, page_size=pagination.page_size
    )
    data = [schemas.CaseOut.model_validate(c).model_dump(mode="json") for c in items]
    return paginated_response(request, data, total, pagination)


@case_router.get("/{case_id}", dependencies=[require_permission("CASE_CREATE")])
async def get_case(
    request: Request,
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    case = await service.get_case(db, case_id)
    data = schemas.CaseOut.model_validate(case).model_dump(mode="json")
    data["assigned_expert_name"] = case.assigned_expert.full_name if case.assigned_expert else None
    return success_response(request, data, headers=etag_headers(case.version))


@case_router.patch("/{case_id}", dependencies=[require_permission("CASE_CREATE")])
async def update_case(
    request: Request,
    case_id: uuid.UUID,
    payload: schemas.CaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    case = await service.update_case(db, case_id, payload)
    data = schemas.CaseOut.model_validate(case).model_dump(mode="json")
    data["assigned_expert_name"] = case.assigned_expert.full_name if case.assigned_expert else None
    return success_response(request, data, headers=etag_headers(case.version))


@case_router.post("/{case_id}/assign-expert", dependencies=[require_permission("CASE_ASSIGN")])
async def assign_expert(
    request: Request,
    case_id: uuid.UUID,
    payload: schemas.AssignExpertRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    case = await service.assign_expert(db, case_id, payload.expert_user_id)
    data = schemas.CaseOut.model_validate(case).model_dump(mode="json")
    data["assigned_expert_name"] = case.assigned_expert.full_name if case.assigned_expert else None
    return success_response(request, data, headers=etag_headers(case.version))


@case_router.post("/{case_id}/change-status", dependencies=[require_permission("CASE_CREATE")])
async def change_status(
    request: Request,
    case_id: uuid.UUID,
    payload: schemas.ChangeStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    case = await service.change_status(db, case_id, payload)
    data = schemas.CaseOut.model_validate(case).model_dump(mode="json")
    data["assigned_expert_name"] = case.assigned_expert.full_name if case.assigned_expert else None
    return success_response(request, data, headers=etag_headers(case.version))


@case_router.get("/{case_id}/timeline", dependencies=[require_permission("CASE_CREATE")])
async def get_timeline(
    request: Request,
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    entries = await service.get_timeline(db, case_id)
    data = [e.model_dump(mode="json") for e in entries]
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# RCA Record router (nested under /cases)
# ═══════════════════════════════════════════════════════════════════

@case_router.get("/{case_id}/rca-records", dependencies=[require_permission("CASE_CREATE")])
async def list_rca_records(
    request: Request,
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await service.list_rca_records(db, case_id)
    data = [schemas.RcaRecordOut.model_validate(r).model_dump(mode="json") for r in items]
    return success_response(request, data)


@case_router.post("/{case_id}/rca-records", dependencies=[require_permission("RCA_WRITE")])
async def create_rca_record(
    request: Request,
    case_id: uuid.UUID,
    payload: schemas.RcaRecordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    rca = await service.create_rca_record(db, case_id, payload, user.id)
    data = schemas.RcaRecordOut.model_validate(rca).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ═══════════════════════════════════════════════════════════════════
# RCA standalone router (for /rca-records/{rca_id} endpoints)
# ═══════════════════════════════════════════════════════════════════

rca_router = APIRouter()


@rca_router.get("/{rca_id}", dependencies=[require_permission("CASE_CREATE")])
async def get_rca_record(
    request: Request,
    rca_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rca = await service.get_rca_record(db, rca_id)
    data = schemas.RcaRecordOut.model_validate(rca).model_dump(mode="json")
    return success_response(request, data)


@rca_router.patch("/{rca_id}", dependencies=[require_permission("RCA_WRITE")])
async def update_rca_record(
    request: Request,
    rca_id: uuid.UUID,
    payload: schemas.RcaRecordUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rca = await service.update_rca_record(db, rca_id, payload)
    data = schemas.RcaRecordOut.model_validate(rca).model_dump(mode="json")
    return success_response(request, data)


@rca_router.post("/{rca_id}/approve", dependencies=[require_permission("RCA_WRITE")])
async def approve_rca_record(
    request: Request,
    rca_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    rca = await service.approve_rca_record(db, rca_id, user.id)
    data = schemas.RcaRecordOut.model_validate(rca).model_dump(mode="json")
    return success_response(request, data)


@rca_router.post("/{rca_id}/factors", dependencies=[require_permission("RCA_WRITE")])
async def create_rca_factor(
    request: Request,
    rca_id: uuid.UUID,
    payload: schemas.RcaFactorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    factor = await service.create_rca_factor(db, rca_id, payload)
    data = schemas.RcaFactorOut.model_validate(factor).model_dump(mode="json")
    return success_response(request, data, status_code=201)


# ═══════════════════════════════════════════════════════════════════
# RCA Factor standalone router (for /rca-factors/{factor_id})
# ═══════════════════════════════════════════════════════════════════

rca_factor_router = APIRouter()


@rca_factor_router.patch("/{factor_id}", dependencies=[require_permission("RCA_WRITE")])
async def update_rca_factor(
    request: Request,
    factor_id: uuid.UUID,
    payload: schemas.RcaFactorUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    factor = await service.update_rca_factor(db, factor_id, payload)
    data = schemas.RcaFactorOut.model_validate(factor).model_dump(mode="json")
    return success_response(request, data)


@rca_factor_router.delete("/{factor_id}", dependencies=[require_permission("RCA_WRITE")])
async def delete_rca_factor(
    request: Request,
    factor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await service.delete_rca_factor(db, factor_id)
    return success_response(request, None)
