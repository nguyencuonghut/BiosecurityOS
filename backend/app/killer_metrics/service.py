"""Service layer for Killer Metrics module (Sprint 04).

Covers: B04.5 Definition CRUD, B04.6 Event CRUD, B04.7 State machine, B04.8 Auto alert.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.killer_metrics.models import KillerMetricDefinition, KillerMetricEvent, KillerEventAttachment
from app.killer_metrics.schemas import (
    KillerMetricDefinitionCreate,
    KillerMetricDefinitionUpdate,
    KillerMetricEventCreate,
    KillerMetricEventUpdate,
    KillerEventAttachmentCreate,
)
from app.shared.exceptions import AppException, ConflictException, NotFoundException
from app.shared.optimistic_lock import apply_version_update, check_version


# ── Valid transitions for killer event state machine (B04.7) ──
VALID_TRANSITIONS: dict[str, list[str]] = {
    "open": ["under_review", "rejected"],
    "under_review": ["controlled", "open", "rejected"],
    "controlled": ["closed", "under_review"],
    # "closed" and "rejected" are terminal
}


# ═══════════════════════════════════════════════════════════════════
# Definition CRUD (B04.5)
# ═══════════════════════════════════════════════════════════════════

VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_PRIORITY = {"P0", "P1", "P2", "P3"}
VALID_DEFINITION_SOURCE_TYPES = {"scorecard_item", "field_report", "both"}


async def list_definitions(db: AsyncSession) -> list[KillerMetricDefinition]:
    result = await db.execute(
        select(KillerMetricDefinition).order_by(KillerMetricDefinition.code)
    )
    return list(result.scalars().all())


async def get_definition(db: AsyncSession, definition_id: uuid.UUID) -> KillerMetricDefinition:
    result = await db.execute(
        select(KillerMetricDefinition).where(KillerMetricDefinition.id == definition_id)
    )
    defn = result.scalar_one_or_none()
    if not defn:
        raise NotFoundException("Killer metric definition not found.")
    return defn


async def create_definition(
    db: AsyncSession, data: KillerMetricDefinitionCreate
) -> KillerMetricDefinition:
    _validate_severity(data.severity_level)
    _validate_priority(data.default_case_priority)
    if hasattr(data, "source_type") and data.source_type:
        _validate_definition_source_type(data.source_type)

    # Check unique code
    existing = await db.execute(
        select(KillerMetricDefinition).where(KillerMetricDefinition.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise AppException(400, "DUPLICATE", f"Mã '{data.code}' đã tồn tại.")

    defn = KillerMetricDefinition(**data.model_dump())
    db.add(defn)
    await db.flush()
    await db.refresh(defn)
    await db.commit()
    return defn


async def update_definition(
    db: AsyncSession, definition_id: uuid.UUID, data: KillerMetricDefinitionUpdate
) -> KillerMetricDefinition:
    defn = await get_definition(db, definition_id)
    update_data = data.model_dump(exclude_unset=True)
    if "severity_level" in update_data:
        _validate_severity(update_data["severity_level"])
    if "default_case_priority" in update_data:
        _validate_priority(update_data["default_case_priority"])
    for key, value in update_data.items():
        setattr(defn, key, value)
    await db.flush()
    await db.refresh(defn)
    await db.commit()
    return defn


# ═══════════════════════════════════════════════════════════════════
# Event CRUD + State Machine (B04.6, B04.7)
# ═══════════════════════════════════════════════════════════════════

async def list_events(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    status: str | None = None,
    definition_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[KillerMetricEvent], int]:
    base = select(KillerMetricEvent).options(selectinload(KillerMetricEvent.definition))
    count_q = select(func.count()).select_from(KillerMetricEvent)

    if farm_id:
        base = base.where(KillerMetricEvent.farm_id == farm_id)
        count_q = count_q.where(KillerMetricEvent.farm_id == farm_id)
    if status:
        base = base.where(KillerMetricEvent.status == status)
        count_q = count_q.where(KillerMetricEvent.status == status)
    if definition_id:
        base = base.where(KillerMetricEvent.definition_id == definition_id)
        count_q = count_q.where(KillerMetricEvent.definition_id == definition_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(KillerMetricEvent.event_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> KillerMetricEvent:
    result = await db.execute(
        select(KillerMetricEvent)
        .options(selectinload(KillerMetricEvent.definition))
        .where(KillerMetricEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise NotFoundException("Killer metric event not found.")
    return event


async def create_event(
    db: AsyncSession, data: KillerMetricEventCreate, detected_by_user_id: uuid.UUID, detected_by_name: str
) -> KillerMetricEvent:
    # Validate definition exists and is active
    defn = await get_definition(db, data.definition_id)
    if not defn.active_flag:
        raise AppException(400, "INACTIVE_DEFINITION", "Killer metric definition is not active.")

    event = KillerMetricEvent(
        farm_id=data.farm_id,
        area_id=data.area_id,
        definition_id=data.definition_id,
        event_at=data.event_at or func.now(),
        detected_by_user_id=detected_by_user_id,
        source_type=data.source_type,
        source_assessment_item_result_id=data.source_assessment_item_result_id,
        summary=data.summary,
        status="open",
        required_case_flag=True,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    # B04.8: Auto alert — create in-app notification for admins/experts
    await _create_killer_alert(db, event, defn, detected_by_name)

    await db.commit()
    # Re-load with relationship
    return await get_event(db, event.id)


async def update_event(
    db: AsyncSession, event_id: uuid.UUID, data: KillerMetricEventUpdate
) -> KillerMetricEvent:
    event = await get_event(db, event_id)
    check_version(event.version, data.version)

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})
    if "status" in update_data:
        _validate_transition(event.status, update_data["status"])

    for key, value in update_data.items():
        setattr(event, key, value)

    event.version = apply_version_update(event.version)
    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        err_msg = str(exc)
        if "risk_case" in err_msg.lower() or "chưa có risk_case" in err_msg:
            raise AppException(
                409,
                "CLOSE_REQUIRES_CASE",
                "Không thể đóng sự kiện killer metric khi chưa có risk_case liên kết.",
            )
        raise
    await db.refresh(event)
    await db.commit()
    return await get_event(db, event.id)


# ═══════════════════════════════════════════════════════════════════
# Auto Notification (B04.8)
# ═══════════════════════════════════════════════════════════════════

async def _create_killer_alert(
    db: AsyncSession,
    event: KillerMetricEvent,
    defn: KillerMetricDefinition,
    detected_by_name: str,
) -> None:
    """Create in_app notification for users with KILLER_EVENT_READ permission (experts + region managers)."""
    from app.auth.models import AppPermission, AppUser, RolePermission, UserRole

    # Find users who should be notified: those with roles that have relevant permissions
    stmt = (
        select(AppUser.id)
        .join(UserRole, UserRole.user_id == AppUser.id)
        .join(RolePermission, RolePermission.role_id == UserRole.role_id)
        .join(AppPermission, AppPermission.id == RolePermission.permission_id)
        .where(AppPermission.code == "KILLER_EVENT_READ")
        .where(AppUser.status == "active")
        .distinct()
    )
    result = await db.execute(stmt)
    recipient_ids = [row[0] for row in result.all()]

    if not recipient_ids:
        return

    # Lazy import to avoid circular dependency
    from app.killer_metrics.notification_model import Notification

    title = f"⚠️ Killer Metric: {defn.name}"
    body = (
        f"Sự kiện killer metric [{defn.code}] được ghi nhận bởi {detected_by_name}. "
        f"Mức độ: {defn.severity_level}. Mô tả: {event.summary[:200]}"
    )

    for uid in recipient_ids:
        notif = Notification(
            recipient_user_id=uid,
            channel="in_app",
            title=title,
            body=body,
            entity_type="killer_metric_event",
            entity_id=event.id,
            status="sent",
        )
        db.add(notif)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════
# Event Attachments (FR-08a)
# ═══════════════════════════════════════════════════════════════════

async def list_event_attachments(db: AsyncSession, event_id: uuid.UUID) -> list[KillerEventAttachment]:
    await get_event(db, event_id)
    from app.attachments.models import Attachment
    result = await db.execute(
        select(KillerEventAttachment)
        .join(KillerEventAttachment.attachment)
        .options(selectinload(KillerEventAttachment.attachment))
        .where(KillerEventAttachment.event_id == event_id)
        .where(Attachment.archived_at.is_(None))
    )
    return list(result.scalars().all())


async def add_event_attachment(
    db: AsyncSession, event_id: uuid.UUID, data: KillerEventAttachmentCreate
) -> KillerEventAttachment:
    await get_event(db, event_id)

    from app.attachments.models import Attachment
    result = await db.execute(select(Attachment).where(Attachment.id == data.attachment_id))
    if not result.scalar_one_or_none():
        raise NotFoundException("Attachment not found.")

    link = KillerEventAttachment(
        event_id=event_id,
        attachment_id=data.attachment_id,
        caption=data.caption,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    await db.commit()
    return link


async def remove_event_attachment(db: AsyncSession, event_id: uuid.UUID, attachment_id: uuid.UUID) -> None:
    await get_event(db, event_id)
    result = await db.execute(
        select(KillerEventAttachment).where(
            KillerEventAttachment.event_id == event_id,
            KillerEventAttachment.attachment_id == attachment_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundException("Attachment link not found.")
    await db.delete(link)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _validate_severity(value: str) -> None:
    if value not in VALID_SEVERITY:
        raise AppException(422, "INVALID_SEVERITY", f"severity_level phải là: {', '.join(sorted(VALID_SEVERITY))}")


def _validate_priority(value: str) -> None:
    if value not in VALID_PRIORITY:
        raise AppException(422, "INVALID_PRIORITY", f"default_case_priority phải là: {', '.join(sorted(VALID_PRIORITY))}")


def _validate_definition_source_type(value: str) -> None:
    if value not in VALID_DEFINITION_SOURCE_TYPES:
        raise AppException(422, "INVALID_SOURCE_TYPE", f"source_type phải là: {', '.join(sorted(VALID_DEFINITION_SOURCE_TYPES))}")


def _validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ConflictException(
            message=f"Không thể chuyển trạng thái từ '{current}' sang '{target}'. "
            f"Cho phép: {', '.join(allowed) if allowed else 'không có'}."
        )
