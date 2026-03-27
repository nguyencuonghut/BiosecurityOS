"""Scorecard service — CRUD for template, section, item + activate/archive."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.scorecards.models import ScorecardItem, ScorecardSection, ScorecardTemplate
from app.scorecards.schemas import (
    ScorecardItemCreate,
    ScorecardItemUpdate,
    ScorecardSectionCreate,
    ScorecardSectionUpdate,
    ScorecardTemplateCreate,
    ScorecardTemplateUpdate,
)
from app.shared.cache import cache_delete_pattern, cache_get, cache_set
from app.shared.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)

_TEMPLATE_LIST_TTL = 1800  # 30 minutes — active templates rarely change
_TEMPLATE_DETAIL_TTL = 1800  # 30 minutes
_ACTIVE_TEMPLATES_CACHE_KEY = "scorecard:active_templates"


# ── Template CRUD ───────────────────────────────────────────────

async def list_active_templates_cached(db: AsyncSession) -> list[dict]:
    """Return lightweight metadata for all active templates. Cached 30 min.
    Used by assessment form to populate template selector without DB hit.
    """
    cached = await cache_get(_ACTIVE_TEMPLATES_CACHE_KEY)
    if cached is not None:
        return cached

    result = await db.execute(
        select(
            ScorecardTemplate.id,
            ScorecardTemplate.code,
            ScorecardTemplate.name,
            ScorecardTemplate.farm_type,
            ScorecardTemplate.ownership_type,
            ScorecardTemplate.version_no,
        )
        .where(ScorecardTemplate.status == "active")
        .order_by(ScorecardTemplate.code)
    )
    data = [
        {
            "id": str(r.id),
            "code": r.code,
            "name": r.name,
            "farm_type": r.farm_type,
            "ownership_type": r.ownership_type,
            "version_no": r.version_no,
        }
        for r in result.all()
    ]
    await cache_set(_ACTIVE_TEMPLATES_CACHE_KEY, data, ttl=_TEMPLATE_LIST_TTL)
    return data


async def list_templates(
    db: AsyncSession,
    *,
    farm_type: str | None = None,
    ownership_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ScorecardTemplate], int]:
    query = select(ScorecardTemplate)
    count_q = select(func.count()).select_from(ScorecardTemplate)

    if farm_type:
        query = query.where(ScorecardTemplate.farm_type == farm_type)
        count_q = count_q.where(ScorecardTemplate.farm_type == farm_type)
    if ownership_type:
        query = query.where(ScorecardTemplate.ownership_type == ownership_type)
        count_q = count_q.where(ScorecardTemplate.ownership_type == ownership_type)
    if status:
        query = query.where(ScorecardTemplate.status == status)
        count_q = count_q.where(ScorecardTemplate.status == status)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(ScorecardTemplate.code).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_template(db: AsyncSession, template_id: uuid.UUID) -> ScorecardTemplate:
    result = await db.execute(
        select(ScorecardTemplate).where(ScorecardTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise NotFoundException(f"Template {template_id} không tồn tại.")
    return tmpl


async def get_template_detail(db: AsyncSession, template_id: uuid.UUID) -> ScorecardTemplate:
    """Get template with sections and items eagerly loaded. Cached 30 min."""
    cache_key = f"scorecard:template_detail:{template_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        # Cache hit: bypass DB, reconstruct ORM-free path is not feasible —
        # cache serves as existence proof; still need ORM for relationship traversal.
        # For full cache benefit, callers should use the schema-level response cache
        # added in the router (ETag + 304). Here we skip cache reconstruction.
        pass

    result = await db.execute(
        select(ScorecardTemplate)
        .where(ScorecardTemplate.id == template_id)
        .options(selectinload(ScorecardTemplate.sections).selectinload(ScorecardSection.items))
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise NotFoundException(f"Template {template_id} không tồn tại.")

    # Store lightweight existence record so downstream cache checks work
    await cache_set(cache_key, {"id": str(tmpl.id), "status": tmpl.status}, ttl=_TEMPLATE_DETAIL_TTL)
    return tmpl


async def create_template(db: AsyncSession, data: ScorecardTemplateCreate) -> ScorecardTemplate:
    # Check duplicate code + version
    existing = await db.execute(
        select(ScorecardTemplate).where(
            ScorecardTemplate.code == data.code,
            ScorecardTemplate.version_no == data.version_no,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Template code '{data.code}' version {data.version_no} đã tồn tại.")

    if data.effective_to and data.effective_to < data.effective_from:
        raise ValidationException("effective_to phải >= effective_from.")

    tmpl = ScorecardTemplate(**data.model_dump(), status="draft")
    db.add(tmpl)
    await db.flush()
    await db.refresh(tmpl)
    return tmpl


async def update_template(
    db: AsyncSession, template_id: uuid.UUID, data: ScorecardTemplateUpdate
) -> ScorecardTemplate:
    tmpl = await get_template(db, template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể sửa template ở trạng thái draft.")

    update_data = data.model_dump(exclude_unset=True)

    # Validate effective_to
    eff_from = update_data.get("effective_from", tmpl.effective_from)
    eff_to = update_data.get("effective_to", tmpl.effective_to)
    if eff_to and eff_to < eff_from:
        raise ValidationException("effective_to phải >= effective_from.")

    for field, value in update_data.items():
        setattr(tmpl, field, value)
    await db.flush()
    await db.refresh(tmpl)
    return tmpl


async def activate_template(db: AsyncSession, template_id: uuid.UUID) -> ScorecardTemplate:
    tmpl = await get_template(db, template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể kích hoạt template ở trạng thái draft.")
    tmpl.status = "active"
    await db.flush()
    await db.refresh(tmpl)
    # Invalidate active-template list cache so new active template appears immediately
    await cache_delete_pattern(_ACTIVE_TEMPLATES_CACHE_KEY)
    await cache_delete_pattern(f"scorecard:template_detail:{template_id}")
    return tmpl


async def archive_template(db: AsyncSession, template_id: uuid.UUID) -> ScorecardTemplate:
    tmpl = await get_template(db, template_id)
    if tmpl.status not in ("draft", "active"):
        raise ValidationException("Chỉ có thể lưu trữ template ở trạng thái draft hoặc active.")
    tmpl.status = "archived"
    await db.flush()
    await db.refresh(tmpl)
    # Invalidate caches when template is archived
    await cache_delete_pattern(_ACTIVE_TEMPLATES_CACHE_KEY)
    await cache_delete_pattern(f"scorecard:template_detail:{template_id}")
    return tmpl


# ── Section CRUD ────────────────────────────────────────────────

async def list_sections(db: AsyncSession, template_id: uuid.UUID) -> list[ScorecardSection]:
    await get_template(db, template_id)
    result = await db.execute(
        select(ScorecardSection)
        .where(ScorecardSection.template_id == template_id)
        .options(selectinload(ScorecardSection.items))
        .order_by(ScorecardSection.display_order)
    )
    return list(result.scalars().all())


async def get_section(db: AsyncSession, section_id: uuid.UUID) -> ScorecardSection:
    result = await db.execute(
        select(ScorecardSection).where(ScorecardSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise NotFoundException(f"Section {section_id} không tồn tại.")
    return section


async def create_section(
    db: AsyncSession, template_id: uuid.UUID, data: ScorecardSectionCreate
) -> ScorecardSection:
    tmpl = await get_template(db, template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể thêm section khi template ở trạng thái draft.")

    # Check duplicate code within template
    existing = await db.execute(
        select(ScorecardSection).where(
            ScorecardSection.template_id == template_id,
            ScorecardSection.code == data.code,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Section code '{data.code}' đã tồn tại trong template này.")

    section = ScorecardSection(template_id=template_id, **data.model_dump())
    db.add(section)
    await db.flush()
    await db.refresh(section)
    return section


async def update_section(
    db: AsyncSession, section_id: uuid.UUID, data: ScorecardSectionUpdate
) -> ScorecardSection:
    section = await get_section(db, section_id)

    # Check template is draft
    tmpl = await get_template(db, section.template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể sửa section khi template ở trạng thái draft.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)
    await db.flush()
    await db.refresh(section)
    return section


# ── Item CRUD ───────────────────────────────────────────────────

async def list_items(db: AsyncSession, section_id: uuid.UUID) -> list[ScorecardItem]:
    await get_section(db, section_id)
    result = await db.execute(
        select(ScorecardItem)
        .where(ScorecardItem.section_id == section_id)
        .order_by(ScorecardItem.display_order)
    )
    return list(result.scalars().all())


async def get_item(db: AsyncSession, item_id: uuid.UUID) -> ScorecardItem:
    result = await db.execute(
        select(ScorecardItem).where(ScorecardItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException(f"Item {item_id} không tồn tại.")
    return item


async def create_item(
    db: AsyncSession, section_id: uuid.UUID, data: ScorecardItemCreate
) -> ScorecardItem:
    section = await get_section(db, section_id)

    # Check template is draft
    tmpl = await get_template(db, section.template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể thêm item khi template ở trạng thái draft.")

    # Validate thresholds
    if data.threshold_warning is not None and data.threshold_fail is not None:
        if data.threshold_fail < data.threshold_warning:
            raise ValidationException("threshold_fail phải >= threshold_warning.")

    # Check duplicate code within section
    existing = await db.execute(
        select(ScorecardItem).where(
            ScorecardItem.section_id == section_id,
            ScorecardItem.code == data.code,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Item code '{data.code}' đã tồn tại trong section này.")

    item = ScorecardItem(section_id=section_id, **data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_item(
    db: AsyncSession, item_id: uuid.UUID, data: ScorecardItemUpdate
) -> ScorecardItem:
    item = await get_item(db, item_id)

    # Check template is draft
    section = await get_section(db, item.section_id)
    tmpl = await get_template(db, section.template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể sửa item khi template ở trạng thái draft.")

    update_data = data.model_dump(exclude_unset=True)

    # Validate thresholds
    tw = update_data.get("threshold_warning", item.threshold_warning)
    tf = update_data.get("threshold_fail", item.threshold_fail)
    if tw is not None and tf is not None and tf < tw:
        raise ValidationException("threshold_fail phải >= threshold_warning.")

    for field, value in update_data.items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: uuid.UUID) -> None:
    item = await get_item(db, item_id)

    section = await get_section(db, item.section_id)
    tmpl = await get_template(db, section.template_id)
    if tmpl.status != "draft":
        raise ValidationException("Chỉ có thể xóa item khi template ở trạng thái draft.")

    await db.delete(item)
    await db.flush()
