"""Service layer for Scar Memory module (Sprint 07)."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.scars.models import ScarLink, ScarRecord
from app.scars.schemas import (
    VALID_CONFIDENCE_LEVELS,
    VALID_LINK_TYPES,
    VALID_SCAR_TYPES,
    ScarCreate,
    ScarLinkCreate,
    ScarUpdate,
)
from app.shared.exceptions import AppException, NotFoundException


# ═══════════════════════════════════════════════════════════════════
# Scar Record CRUD
# ═══════════════════════════════════════════════════════════════════

async def list_scars(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    scar_type: str | None = None,
    confidence_level: str | None = None,
    status: str | None = None,
    area_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ScarRecord], int]:
    base = select(ScarRecord).where(ScarRecord.archived_at.is_(None))
    count_q = select(func.count()).select_from(ScarRecord).where(ScarRecord.archived_at.is_(None))

    if farm_id:
        base = base.where(ScarRecord.farm_id == farm_id)
        count_q = count_q.where(ScarRecord.farm_id == farm_id)
    if scar_type:
        base = base.where(ScarRecord.scar_type == scar_type)
        count_q = count_q.where(ScarRecord.scar_type == scar_type)
    if confidence_level:
        base = base.where(ScarRecord.confidence_level == confidence_level)
        count_q = count_q.where(ScarRecord.confidence_level == confidence_level)
    if status:
        base = base.where(ScarRecord.status == status)
        count_q = count_q.where(ScarRecord.status == status)
    if area_id:
        base = base.where(ScarRecord.area_id == area_id)
        count_q = count_q.where(ScarRecord.area_id == area_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(ScarRecord.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_scar(
    db: AsyncSession, data: ScarCreate, created_by_user_id: uuid.UUID
) -> ScarRecord:
    if data.scar_type not in VALID_SCAR_TYPES:
        raise AppException(422, "INVALID_SCAR_TYPE",
                           f"scar_type phải là: {', '.join(VALID_SCAR_TYPES)}")
    if data.confidence_level not in VALID_CONFIDENCE_LEVELS:
        raise AppException(422, "INVALID_CONFIDENCE_LEVEL",
                           f"confidence_level phải là: {', '.join(VALID_CONFIDENCE_LEVELS)}")

    # Recurrence detection: check existing scars with same area + type
    recurrence_count = 0
    if data.area_id and data.scar_type:
        count_result = await db.execute(
            select(func.count()).select_from(ScarRecord).where(
                ScarRecord.farm_id == data.farm_id,
                ScarRecord.area_id == data.area_id,
                ScarRecord.scar_type == data.scar_type,
                ScarRecord.archived_at.is_(None),
            )
        )
        recurrence_count = count_result.scalar() or 0

    scar = ScarRecord(
        farm_id=data.farm_id,
        floorplan_version_id=data.floorplan_version_id,
        area_id=data.area_id,
        scar_type=data.scar_type,
        title=data.title,
        description=data.description,
        source_of_risk=data.source_of_risk,
        confidence_level=data.confidence_level,
        event_date=data.event_date,
        x_percent=data.x_percent,
        y_percent=data.y_percent,
        recurrence_flag=data.recurrence_flag or recurrence_count > 0,
        recurrence_count=recurrence_count,
        created_by_user_id=created_by_user_id,
    )
    db.add(scar)
    await db.flush()
    await db.commit()
    return await get_scar(db, scar.id)


async def get_scar(db: AsyncSession, scar_id: uuid.UUID) -> ScarRecord:
    result = await db.execute(
        select(ScarRecord)
        .options(selectinload(ScarRecord.links))
        .where(ScarRecord.id == scar_id)
    )
    scar = result.scalar_one_or_none()
    if not scar:
        raise NotFoundException("Scar record not found.")
    return scar


async def update_scar(
    db: AsyncSession, scar_id: uuid.UUID, data: ScarUpdate
) -> ScarRecord:
    scar = await get_scar(db, scar_id)

    updates = data.model_dump(exclude_unset=True)

    if "confidence_level" in updates and updates["confidence_level"] not in VALID_CONFIDENCE_LEVELS:
        raise AppException(422, "INVALID_CONFIDENCE_LEVEL",
                           f"confidence_level phải là: {', '.join(VALID_CONFIDENCE_LEVELS)}")

    if "status" in updates and updates["status"] not in ("active", "archived", "obsolete"):
        raise AppException(422, "INVALID_STATUS", "status phải là: active, archived, obsolete")

    for field, value in updates.items():
        setattr(scar, field, value)

    await db.flush()
    await db.commit()
    return await get_scar(db, scar_id)


# ═══════════════════════════════════════════════════════════════════
# Validate Scar (B07.4)
# ═══════════════════════════════════════════════════════════════════

async def validate_scar(
    db: AsyncSession, scar_id: uuid.UUID, validated_by_user_id: uuid.UUID
) -> ScarRecord:
    scar = await get_scar(db, scar_id)

    if scar.confidence_level == "confirmed":
        raise AppException(422, "ALREADY_CONFIRMED", "Scar đã ở trạng thái confirmed.")

    scar.confidence_level = "confirmed"
    scar.validated_by_user_id = validated_by_user_id
    scar.validated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.commit()
    return await get_scar(db, scar_id)


# ═══════════════════════════════════════════════════════════════════
# Scar Links (B07.5)
# ═══════════════════════════════════════════════════════════════════

async def add_scar_link(
    db: AsyncSession, scar_id: uuid.UUID, data: ScarLinkCreate
) -> ScarLink:
    await get_scar(db, scar_id)

    if data.linked_object_type not in VALID_LINK_TYPES:
        raise AppException(422, "INVALID_LINK_TYPE",
                           f"linked_object_type phải là: {', '.join(VALID_LINK_TYPES)}")

    # Validate linked object exists at app layer (BR-08)
    await _validate_linked_object(db, data.linked_object_type, data.linked_object_id)

    # Check duplicate
    dup = await db.execute(
        select(ScarLink).where(
            ScarLink.scar_id == scar_id,
            ScarLink.linked_object_type == data.linked_object_type,
            ScarLink.linked_object_id == data.linked_object_id,
        )
    )
    if dup.scalar_one_or_none():
        raise AppException(409, "DUPLICATE_LINK", "Liên kết này đã tồn tại.")

    link = ScarLink(
        scar_id=scar_id,
        linked_object_type=data.linked_object_type,
        linked_object_id=data.linked_object_id,
        link_reason=data.link_reason,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    await db.commit()
    return link


async def _validate_linked_object(db: AsyncSession, obj_type: str, obj_id: uuid.UUID) -> None:
    """Validate that the linked object exists (BR-08)."""
    if obj_type == "case":
        from app.cases.models import RiskCase
        result = await db.execute(select(RiskCase).where(RiskCase.id == obj_id))
    elif obj_type == "task":
        from app.tasks.models import CorrectiveTask
        result = await db.execute(select(CorrectiveTask).where(CorrectiveTask.id == obj_id))
    elif obj_type == "assessment":
        from app.assessments.models import Assessment
        result = await db.execute(select(Assessment).where(Assessment.id == obj_id))
    elif obj_type == "attachment":
        from app.attachments.models import Attachment
        result = await db.execute(select(Attachment).where(Attachment.id == obj_id))
    else:
        raise AppException(422, "INVALID_LINK_TYPE", f"Loại liên kết không hợp lệ: {obj_type}")

    if not result.scalar_one_or_none():
        raise NotFoundException(f"Đối tượng liên kết ({obj_type}) không tìm thấy.")


# ═══════════════════════════════════════════════════════════════════
# Scar Map Data (B07.6)
# ═══════════════════════════════════════════════════════════════════

async def get_scar_map(
    db: AsyncSession,
    farm_id: uuid.UUID,
    *,
    scar_type: str | None = None,
    confidence_level: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """Return floorplan + scars + markers for a farm's scar map."""
    from app.floorplans.models import FloorplanVersion

    # Get active floorplan
    fp_result = await db.execute(
        select(FloorplanVersion).where(
            FloorplanVersion.farm_id == farm_id,
            FloorplanVersion.status == "active",
        )
    )
    floorplan = fp_result.scalar_one_or_none()

    # Get markers if floorplan exists
    markers = []
    if floorplan:
        from app.floorplans.models import FloorplanMarker
        marker_result = await db.execute(
            select(FloorplanMarker).where(
                FloorplanMarker.floorplan_version_id == floorplan.id
            )
        )
        markers = list(marker_result.scalars().all())

    # Get scars
    scar_q = select(ScarRecord).where(
        ScarRecord.farm_id == farm_id,
        ScarRecord.archived_at.is_(None),
    )
    if scar_type:
        scar_q = scar_q.where(ScarRecord.scar_type == scar_type)
    if confidence_level:
        scar_q = scar_q.where(ScarRecord.confidence_level == confidence_level)
    if date_from:
        scar_q = scar_q.where(ScarRecord.event_date >= date_from)
    if date_to:
        scar_q = scar_q.where(ScarRecord.event_date <= date_to)

    scar_result = await db.execute(scar_q.order_by(ScarRecord.event_date.desc()))
    scars = list(scar_result.scalars().all())

    return {
        "floorplan": floorplan,
        "markers": markers,
        "scars": scars,
    }
