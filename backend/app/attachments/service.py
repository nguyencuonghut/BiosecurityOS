"""Service layer for Attachment / Evidence module (Sprint 06).

Covers: B06.7–B06.11 — Presigned URL, finalize, download, soft delete, file policy.
"""

import hashlib
import uuid
from datetime import datetime, timezone

from miniopy_async import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attachments import file_policy
from app.attachments.models import Attachment
from app.attachments.schemas import FinalizeRequest, PresignRequest
from app.config import settings
from app.shared.exceptions import AppException, NotFoundException


def _get_minio_client() -> Minio:
    """Create MinIO async client from settings."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def _generate_object_key(file_name: str, entity_type: str | None = None, entity_id: uuid.UUID | None = None) -> str:
    """Generate a unique object key with logical folder structure."""
    ts = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    unique_id = uuid.uuid4().hex[:12]
    # Sanitize file_name: only keep the last segment after /
    safe_name = file_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    if entity_type and entity_id:
        return f"{entity_type}/{entity_id}/{ts}/{unique_id}_{safe_name}"
    return f"general/{ts}/{unique_id}_{safe_name}"


# ═══════════════════════════════════════════════════════════════════
# Presigned Upload URL (B06.7)
# ═══════════════════════════════════════════════════════════════════

async def presign_upload(
    db: AsyncSession, data: PresignRequest, uploaded_by_user_id: uuid.UUID
) -> dict:
    """Generate presigned PUT URL and create a pending attachment record."""
    file_policy.validate_mime_type(data.mime_type)

    object_key = _generate_object_key(data.file_name, data.entity_type, data.entity_id)
    bucket = settings.MINIO_BUCKET

    # Create attachment record with file_size_bytes=0 (will be updated on finalize)
    attachment = Attachment(
        storage_bucket=bucket,
        object_key=object_key,
        file_name_original=data.file_name,
        mime_type=data.mime_type,
        file_size_bytes=0,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)

    # Generate presigned PUT URL
    client = _get_minio_client()

    # Ensure bucket exists
    found = await client.bucket_exists(bucket)
    if not found:
        await client.make_bucket(bucket)

    from datetime import timedelta
    upload_url = await client.presigned_put_object(
        bucket, object_key, expires=timedelta(hours=1)
    )

    await db.commit()
    return {
        "attachment_id": attachment.id,
        "upload_url": upload_url,
        "object_key": object_key,
    }


# ═══════════════════════════════════════════════════════════════════
# Finalize Upload (B06.8)
# ═══════════════════════════════════════════════════════════════════

async def finalize_upload(
    db: AsyncSession, attachment_id: uuid.UUID, data: FinalizeRequest
) -> Attachment:
    """Confirm upload complete: validate policy, compute SHA256, store metadata."""
    attachment = await get_attachment(db, attachment_id)

    if attachment.file_size_bytes > 0:
        raise AppException(409, "ALREADY_FINALIZED", "Attachment đã được finalize trước đó.")

    # Validate file size against policy
    file_policy.validate_file_size(attachment.mime_type, data.file_size_bytes)

    # Compute SHA256 hash from MinIO object
    sha256_hash = await _compute_sha256(attachment.storage_bucket, attachment.object_key)

    attachment.file_size_bytes = data.file_size_bytes
    attachment.sha256_hash = sha256_hash
    attachment.captured_at = data.captured_at
    attachment.latitude = data.latitude
    attachment.longitude = data.longitude
    attachment.watermark_text = data.watermark_text

    await db.flush()
    await db.refresh(attachment)
    await db.commit()
    return attachment


async def _compute_sha256(bucket: str, object_key: str) -> str:
    """Download object from MinIO and compute SHA256 hash."""
    client = _get_minio_client()
    try:
        response = await client.get_object(bucket, object_key)
        sha256 = hashlib.sha256()
        async for chunk in response.stream(8192):
            sha256.update(chunk)
        response.close()
        await response.release()
        return sha256.hexdigest()
    except Exception:
        # If object doesn't exist or MinIO unreachable, skip hash
        return ""


# ═══════════════════════════════════════════════════════════════════
# Get / Download (B06.9)
# ═══════════════════════════════════════════════════════════════════

async def get_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> Attachment:
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise NotFoundException("Attachment not found.")
    return attachment


async def get_download_url(db: AsyncSession, attachment_id: uuid.UUID) -> dict:
    """Generate presigned GET URL for downloading."""
    attachment = await get_attachment(db, attachment_id)

    if attachment.archived_at is not None:
        raise AppException(410, "ATTACHMENT_ARCHIVED", "Attachment đã bị xóa.")

    client = _get_minio_client()

    from datetime import timedelta
    from urllib.parse import quote

    download_url = await client.presigned_get_object(
        attachment.storage_bucket,
        attachment.object_key,
        expires=timedelta(hours=1),
        response_headers={
            "response-content-disposition": f'attachment; filename="{quote(attachment.file_name_original)}"'
        },
    )

    return {
        "download_url": download_url,
        "file_name": attachment.file_name_original,
        "mime_type": attachment.mime_type,
    }


# ═══════════════════════════════════════════════════════════════════
# Soft Delete (B06.10)
# ═══════════════════════════════════════════════════════════════════

async def soft_delete_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> Attachment:
    """Soft delete: set archived_at. Physical file is NOT removed."""
    attachment = await get_attachment(db, attachment_id)

    if attachment.archived_at is not None:
        raise AppException(409, "ALREADY_ARCHIVED", "Attachment đã bị xóa trước đó.")

    # Check if attachment is linked to any reviewed task (cannot delete evidence after review)
    from app.tasks.models import TaskAttachment, TaskReview
    result = await db.execute(
        select(TaskAttachment)
        .join(TaskReview, TaskReview.task_id == TaskAttachment.task_id)
        .where(
            TaskAttachment.attachment_id == attachment_id,
            TaskReview.review_result == "approved",
        )
    )
    if result.scalar_one_or_none():
        raise AppException(
            422,
            "EVIDENCE_REVIEWED",
            "Không thể xóa bằng chứng đã được approved review.",
        )

    attachment.archived_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(attachment)
    await db.commit()
    return attachment
