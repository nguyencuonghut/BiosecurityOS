"""Region service — CRUD operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Region
from app.regions.schemas import RegionCreate, RegionUpdate
from app.shared.exceptions import ConflictException, NotFoundException


async def list_regions(
    db: AsyncSession,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Region], int]:
    query = select(Region)
    count_query = select(func.count()).select_from(Region)

    if status:
        query = query.where(Region.status == status)
        count_query = count_query.where(Region.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Region.code).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_region(db: AsyncSession, region_id: uuid.UUID) -> Region:
    result = await db.execute(select(Region).where(Region.id == region_id))
    region = result.scalar_one_or_none()
    if not region:
        raise NotFoundException(f"Region {region_id} không tồn tại.")
    return region


async def create_region(db: AsyncSession, data: RegionCreate) -> Region:
    # Check duplicate code
    existing = await db.execute(select(Region).where(Region.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Region code '{data.code}' đã tồn tại.")

    region = Region(**data.model_dump())
    db.add(region)
    await db.flush()
    return region


async def update_region(db: AsyncSession, region_id: uuid.UUID, data: RegionUpdate) -> Region:
    region = await get_region(db, region_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(region, field, value)
    await db.flush()
    return region
