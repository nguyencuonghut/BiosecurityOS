"""Farm service — CRUD for farm, area, route, external risk point."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AppUser, Farm
from app.farms.models import AreaType, ExternalRiskPoint, FarmArea, FarmRoute
from app.farms.schemas import (
    AreaCreate,
    AreaTypeCreate,
    AreaTypeOut,
    AreaTypeUpdate,
    AreaUpdate,
    ExternalRiskPointCreate,
    FarmCreate,
    FarmUpdate,
    RouteCreate,
)
from app.shared.exceptions import ConflictException, NotFoundException, ValidationException


# ── Scope filter helper ─────────────────────────────────────────

def _apply_farm_scope(query, user: AppUser):
    """Filter farms by user's RBAC scope (region/farm)."""
    if user.farm_id:
        return query.where(Farm.id == user.farm_id)
    if user.region_id:
        return query.where(Farm.region_id == user.region_id)
    return query  # global scope (admin/expert)


# ── Farm CRUD ───────────────────────────────────────────────────

async def list_farms(
    db: AsyncSession,
    user: AppUser,
    *,
    region_id: uuid.UUID | None = None,
    farm_type: str | None = None,
    ownership_type: str | None = None,
    operational_status: str | None = None,
    baseline_risk_level: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Farm], int]:
    query = select(Farm)
    count_query = select(func.count()).select_from(Farm)

    # RBAC scope
    query = _apply_farm_scope(query, user)
    count_query = _apply_farm_scope(count_query, user)

    if region_id:
        query = query.where(Farm.region_id == region_id)
        count_query = count_query.where(Farm.region_id == region_id)
    if farm_type:
        query = query.where(Farm.farm_type == farm_type)
        count_query = count_query.where(Farm.farm_type == farm_type)
    if ownership_type:
        query = query.where(Farm.ownership_type == ownership_type)
        count_query = count_query.where(Farm.ownership_type == ownership_type)
    if operational_status:
        query = query.where(Farm.operational_status == operational_status)
        count_query = count_query.where(Farm.operational_status == operational_status)
    if baseline_risk_level:
        query = query.where(Farm.baseline_risk_level == baseline_risk_level)
        count_query = count_query.where(Farm.baseline_risk_level == baseline_risk_level)
    if search:
        pattern = f"%{search}%"
        search_filter = or_(Farm.code.ilike(pattern), Farm.name.ilike(pattern))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Farm.code).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_farm(db: AsyncSession, farm_id: uuid.UUID) -> Farm:
    result = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise NotFoundException(f"Farm {farm_id} không tồn tại.")
    return farm


async def create_farm(db: AsyncSession, data: FarmCreate) -> Farm:
    # Check duplicate code
    existing = await db.execute(select(Farm).where(Farm.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Farm code '{data.code}' đã tồn tại.")

    farm = Farm(**data.model_dump())
    db.add(farm)
    await db.flush()
    return farm


async def update_farm(db: AsyncSession, farm_id: uuid.UUID, data: FarmUpdate) -> Farm:
    farm = await get_farm(db, farm_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm, field, value)
    await db.flush()
    return farm


# ── Area Type ───────────────────────────────────────────────────

async def list_area_types(db: AsyncSession) -> list[AreaType]:
    result = await db.execute(select(AreaType).order_by(AreaType.display_order, AreaType.name))
    return list(result.scalars().all())


async def create_area_type(db: AsyncSession, payload: AreaTypeCreate) -> AreaType:
    existing = await db.execute(select(AreaType).where(AreaType.code == payload.code))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Mã loại khu vực '{payload.code}' đã tồn tại.")
    obj = AreaType(code=payload.code, name=payload.name, display_order=payload.display_order)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_area_type(db: AsyncSession, area_type_id: uuid.UUID, payload: AreaTypeUpdate) -> AreaType:
    result = await db.execute(select(AreaType).where(AreaType.id == area_type_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise NotFoundException("Không tìm thấy loại khu vực.")
    if payload.code is not None and payload.code != obj.code:
        dup = await db.execute(select(AreaType).where(AreaType.code == payload.code))
        if dup.scalar_one_or_none():
            raise ConflictException(f"Mã loại khu vực '{payload.code}' đã tồn tại.")
        obj.code = payload.code
    if payload.name is not None:
        obj.name = payload.name
    if payload.display_order is not None:
        obj.display_order = payload.display_order
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_area_type(db: AsyncSession, area_type_id: uuid.UUID) -> None:
    result = await db.execute(select(AreaType).where(AreaType.id == area_type_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise NotFoundException("Không tìm thấy loại khu vực.")
    await db.delete(obj)
    await db.flush()


# ── Farm Area ───────────────────────────────────────────────────

async def list_areas(db: AsyncSession, farm_id: uuid.UUID) -> list[FarmArea]:
    await get_farm(db, farm_id)  # ensure farm exists
    result = await db.execute(
        select(FarmArea).where(FarmArea.farm_id == farm_id).order_by(FarmArea.code)
    )
    return list(result.scalars().all())


async def create_area(db: AsyncSession, farm_id: uuid.UUID, data: AreaCreate) -> FarmArea:
    await get_farm(db, farm_id)

    # Check duplicate code within farm
    existing = await db.execute(
        select(FarmArea).where(FarmArea.farm_id == farm_id, FarmArea.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Area code '{data.code}' đã tồn tại trong farm này.")

    # Validate parent belongs to same farm
    if data.parent_area_id:
        parent = await db.execute(
            select(FarmArea).where(FarmArea.id == data.parent_area_id, FarmArea.farm_id == farm_id)
        )
        if not parent.scalar_one_or_none():
            raise ValidationException("parent_area_id không thuộc cùng farm.")

    area = FarmArea(farm_id=farm_id, **data.model_dump())
    db.add(area)
    await db.flush()
    return area


async def update_area(db: AsyncSession, farm_id: uuid.UUID, area_id: uuid.UUID, data: AreaUpdate) -> FarmArea:
    result = await db.execute(
        select(FarmArea).where(FarmArea.id == area_id, FarmArea.farm_id == farm_id)
    )
    area = result.scalar_one_or_none()
    if not area:
        raise NotFoundException(f"Area {area_id} không tồn tại trong farm {farm_id}.")

    # Validate parent
    update_data = data.model_dump(exclude_unset=True)
    if "parent_area_id" in update_data and update_data["parent_area_id"]:
        if update_data["parent_area_id"] == area_id:
            raise ValidationException("Area không thể là parent của chính nó.")
        parent = await db.execute(
            select(FarmArea).where(
                FarmArea.id == update_data["parent_area_id"], FarmArea.farm_id == farm_id
            )
        )
        if not parent.scalar_one_or_none():
            raise ValidationException("parent_area_id không thuộc cùng farm.")

    for field, value in update_data.items():
        setattr(area, field, value)
    await db.flush()
    return area


# ── Farm Route ──────────────────────────────────────────────────

async def list_routes(db: AsyncSession, farm_id: uuid.UUID) -> list[FarmRoute]:
    await get_farm(db, farm_id)
    result = await db.execute(
        select(FarmRoute).where(FarmRoute.farm_id == farm_id).order_by(FarmRoute.created_at)
    )
    return list(result.scalars().all())


async def create_route(db: AsyncSession, farm_id: uuid.UUID, data: RouteCreate) -> FarmRoute:
    await get_farm(db, farm_id)

    if data.from_area_id == data.to_area_id:
        raise ValidationException("from_area_id và to_area_id phải khác nhau.")

    # Validate both areas belong to same farm
    for area_id in [data.from_area_id, data.to_area_id]:
        result = await db.execute(
            select(FarmArea).where(FarmArea.id == area_id, FarmArea.farm_id == farm_id)
        )
        if not result.scalar_one_or_none():
            raise ValidationException(f"Area {area_id} không thuộc farm {farm_id}.")

    route = FarmRoute(farm_id=farm_id, **data.model_dump())
    db.add(route)
    await db.flush()
    return route


# ── External Risk Point ─────────────────────────────────────────

async def list_risk_points(db: AsyncSession, farm_id: uuid.UUID) -> list[ExternalRiskPoint]:
    await get_farm(db, farm_id)
    result = await db.execute(
        select(ExternalRiskPoint)
        .where(ExternalRiskPoint.farm_id == farm_id)
        .order_by(ExternalRiskPoint.created_at)
    )
    return list(result.scalars().all())


async def create_risk_point(
    db: AsyncSession, farm_id: uuid.UUID, data: ExternalRiskPointCreate
) -> ExternalRiskPoint:
    await get_farm(db, farm_id)
    risk_point = ExternalRiskPoint(farm_id=farm_id, **data.model_dump())
    db.add(risk_point)
    await db.flush()
    return risk_point
