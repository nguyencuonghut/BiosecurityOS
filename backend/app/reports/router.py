"""Report router (B10.1, B10.2, B10.3)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.reports import service
from app.reports.schemas import ReportCreateRequest, ReportOut
from app.shared.exceptions import success_response
from app.shared.pagination import PaginationParams, paginated_response

router = APIRouter()


@router.get(
    "",
    dependencies=[require_permission("REPORT_GENERATE")],
)
async def list_reports(
    request: Request,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List current user's reports."""
    rows, total = await service.list_reports(
        db,
        requested_by=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items = [ReportOut.model_validate(r).model_dump(mode="json") for r in rows]
    return paginated_response(request, items, total, pagination)


@router.post(
    "",
    dependencies=[require_permission("REPORT_GENERATE")],
    status_code=201,
)
async def create_report(
    request: Request,
    body: ReportCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate a report (synchronous in Phase 1)."""
    report = await service.create_report(
        db,
        requested_by=current_user.id,
        report_type=body.report_type,
        fmt=body.format,
        filters=body.filters,
    )
    data = ReportOut.model_validate(report).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@router.get(
    "/{report_id}",
    dependencies=[require_permission("REPORT_GENERATE")],
)
async def get_report(
    request: Request,
    report_id: uuid.UUID,
    _current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get report status."""
    report = await service.get_report(db, report_id)
    data = ReportOut.model_validate(report).model_dump(mode="json")
    return success_response(request, data)


@router.get(
    "/{report_id}/download",
    dependencies=[require_permission("REPORT_GENERATE")],
)
async def download_report(
    report_id: uuid.UUID,
    _current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download generated report file (XLSX, CSV)."""
    content, content_type, filename = await service.generate_download(db, report_id)
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
