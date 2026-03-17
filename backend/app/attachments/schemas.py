"""Pydantic schemas for Attachment / Evidence module (Sprint 06)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ═══════════════════════════════════════════════════════════════════
# Presign request/response
# ═══════════════════════════════════════════════════════════════════

class PresignRequest(BaseModel):
    file_name: str
    mime_type: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None


class PresignResponse(BaseModel):
    attachment_id: uuid.UUID
    upload_url: str
    object_key: str


# ═══════════════════════════════════════════════════════════════════
# Finalize request
# ═══════════════════════════════════════════════════════════════════

class FinalizeRequest(BaseModel):
    file_size_bytes: int
    captured_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    watermark_text: str | None = None


# ═══════════════════════════════════════════════════════════════════
# Attachment output
# ═══════════════════════════════════════════════════════════════════

class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    storage_bucket: str
    object_key: str
    file_name_original: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str | None
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    watermark_text: str | None
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime
    is_original_file: bool
    parent_attachment_id: uuid.UUID | None
    archived_at: datetime | None


class DownloadResponse(BaseModel):
    download_url: str
    file_name: str
    mime_type: str
