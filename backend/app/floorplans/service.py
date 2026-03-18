"""Service layer for Floorplan / Digital Twin module (Sprint 07)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.floorplans.models import FloorplanMarker, FloorplanVersion
from app.floorplans.schemas import (
    FloorplanVersionCreate,
    FloorplanVersionUpdate,
    MarkerCreate,
    MarkerUpdate,
)
from app.shared.exceptions import AppException, NotFoundException


# ═══════════════════════════════════════════════════════════════════
# Floorplan Version CRUD
# ═══════════════════════════════════════════════════════════════════

async def list_floorplans(db: AsyncSession, farm_id: uuid.UUID) -> list[FloorplanVersion]:
    result = await db.execute(
        select(FloorplanVersion)
        .where(FloorplanVersion.farm_id == farm_id)
        .order_by(FloorplanVersion.version_no.desc())
    )
    return list(result.scalars().all())


async def create_floorplan(
    db: AsyncSession, farm_id: uuid.UUID, data: FloorplanVersionCreate
) -> FloorplanVersion:
    # Auto-increment version_no
    max_ver = await db.execute(
        select(func.coalesce(func.max(FloorplanVersion.version_no), 0))
        .where(FloorplanVersion.farm_id == farm_id)
    )
    next_ver = max_ver.scalar() + 1

    fp = FloorplanVersion(
        farm_id=farm_id,
        version_no=next_ver,
        title=data.title,
        effective_from=data.effective_from,
        plan_file_attachment_id=data.plan_file_attachment_id,
        status="draft",
    )
    db.add(fp)
    await db.flush()
    await db.refresh(fp)
    await db.commit()
    return fp


async def get_floorplan(db: AsyncSession, floorplan_id: uuid.UUID) -> FloorplanVersion:
    result = await db.execute(
        select(FloorplanVersion)
        .options(selectinload(FloorplanVersion.markers))
        .where(FloorplanVersion.id == floorplan_id)
    )
    fp = result.scalar_one_or_none()
    if not fp:
        raise NotFoundException("Floorplan version not found.")
    return fp


async def update_floorplan(
    db: AsyncSession, floorplan_id: uuid.UUID, data: FloorplanVersionUpdate
) -> FloorplanVersion:
    fp = await get_floorplan(db, floorplan_id)
    if fp.status != "draft":
        raise AppException(422, "NOT_DRAFT", "Chỉ có thể sửa floorplan ở trạng thái draft.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fp, field, value)

    await db.flush()
    await db.refresh(fp)
    await db.commit()
    return fp


async def approve_floorplan(
    db: AsyncSession, floorplan_id: uuid.UUID, approved_by_user_id: uuid.UUID
) -> FloorplanVersion:
    fp = await get_floorplan(db, floorplan_id)
    if fp.status != "draft":
        raise AppException(422, "NOT_DRAFT", "Chỉ draft mới được approve.")

    # Archive any currently active floorplan for same farm
    active_result = await db.execute(
        select(FloorplanVersion).where(
            FloorplanVersion.farm_id == fp.farm_id,
            FloorplanVersion.status == "active",
        )
    )
    for active_fp in active_result.scalars().all():
        active_fp.status = "archived"
        active_fp.effective_to = fp.effective_from

    fp.status = "active"
    fp.approved_by = approved_by_user_id
    fp.approved_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(fp)
    await db.commit()
    return fp


# ═══════════════════════════════════════════════════════════════════
# Floorplan Marker CRUD
# ═══════════════════════════════════════════════════════════════════

async def list_markers(db: AsyncSession, floorplan_id: uuid.UUID) -> list[FloorplanMarker]:
    await get_floorplan(db, floorplan_id)
    result = await db.execute(
        select(FloorplanMarker)
        .where(FloorplanMarker.floorplan_version_id == floorplan_id)
        .order_by(FloorplanMarker.created_at)
    )
    return list(result.scalars().all())


async def create_marker(
    db: AsyncSession, floorplan_id: uuid.UUID, data: MarkerCreate
) -> FloorplanMarker:
    await get_floorplan(db, floorplan_id)
    marker = FloorplanMarker(
        floorplan_version_id=floorplan_id,
        area_id=data.area_id,
        marker_type=data.marker_type,
        label=data.label,
        x_percent=data.x_percent,
        y_percent=data.y_percent,
        metadata_json=data.metadata_json,
    )
    db.add(marker)
    await db.flush()
    await db.refresh(marker)
    await db.commit()
    return marker


async def get_marker(db: AsyncSession, marker_id: uuid.UUID) -> FloorplanMarker:
    result = await db.execute(
        select(FloorplanMarker).where(FloorplanMarker.id == marker_id)
    )
    marker = result.scalar_one_or_none()
    if not marker:
        raise NotFoundException("Floorplan marker not found.")
    return marker


async def update_marker(
    db: AsyncSession, marker_id: uuid.UUID, data: MarkerUpdate
) -> FloorplanMarker:
    marker = await get_marker(db, marker_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(marker, field, value)
    await db.flush()
    await db.refresh(marker)
    await db.commit()
    return marker


async def delete_marker(db: AsyncSession, marker_id: uuid.UUID) -> None:
    marker = await get_marker(db, marker_id)
    await db.delete(marker)
    await db.commit()
