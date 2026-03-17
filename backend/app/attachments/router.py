"""API routers for Attachment / Evidence module (Sprint 06)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.attachments import schemas, service
from app.auth.dependencies import CurrentUser, require_permission
from app.database import get_db
from app.shared.exceptions import success_response


attachment_router = APIRouter()


@attachment_router.post("/presign", dependencies=[require_permission("ATTACHMENT_UPLOAD")])
async def presign_upload(
    request: Request,
    payload: schemas.PresignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
):
    result = await service.presign_upload(db, payload, user.id)
    data = schemas.PresignResponse(**result).model_dump(mode="json")
    return success_response(request, data, status_code=201)


@attachment_router.post("/{attachment_id}/finalize", dependencies=[require_permission("ATTACHMENT_UPLOAD")])
async def finalize_upload(
    request: Request,
    attachment_id: uuid.UUID,
    payload: schemas.FinalizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    attachment = await service.finalize_upload(db, attachment_id, payload)
    data = schemas.AttachmentOut.model_validate(attachment).model_dump(mode="json")
    return success_response(request, data)


@attachment_router.get("/{attachment_id}", dependencies=[require_permission("ATTACHMENT_READ")])
async def get_attachment(
    request: Request,
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    attachment = await service.get_attachment(db, attachment_id)
    data = schemas.AttachmentOut.model_validate(attachment).model_dump(mode="json")
    return success_response(request, data)


@attachment_router.get("/{attachment_id}/download", dependencies=[require_permission("ATTACHMENT_READ")])
async def download_attachment(
    request: Request,
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await service.get_download_url(db, attachment_id)
    data = schemas.DownloadResponse(**result).model_dump(mode="json")
    return success_response(request, data)


@attachment_router.delete("/{attachment_id}", dependencies=[require_permission("ATTACHMENT_DELETE")])
async def delete_attachment(
    request: Request,
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    attachment = await service.soft_delete_attachment(db, attachment_id)
    data = schemas.AttachmentOut.model_validate(attachment).model_dump(mode="json")
    return success_response(request, data)
