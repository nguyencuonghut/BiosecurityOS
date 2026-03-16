"""Service layer for Risk Case & RCA module (Sprint 05).

Covers: B05.1–B05.9 — Case CRUD, queue, state machine, RCA CRUD, RCA approve, killer link.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.models import CaseParticipant, RcaFactor, RcaRecord, RiskCase
from app.cases.schemas import (
    CaseCreate,
    CaseUpdate,
    ChangeStatusRequest,
    RcaFactorCreate,
    RcaFactorUpdate,
    RcaRecordCreate,
    RcaRecordUpdate,
    TimelineEntry,
)
from app.shared.exceptions import AppException, ConflictException, ForbiddenException, NotFoundException
from app.shared.optimistic_lock import apply_version_update, check_version


# ── Constants ──

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_CASE_TYPES = {"low_score", "killer_event", "scar", "manual"}
VALID_RCA_METHODS = {"5_why", "fishbone", "capa", "other"}
VALID_CONFIDENCE = {"low", "medium", "high", "confirmed"}
VALID_FACTOR_GROUPS = {"people", "process", "place", "equipment", "environment", "monitoring", "external"}
VALID_PARTICIPANT_ROLES = {"owner", "reviewer", "observer", "farm_contact"}

VALID_TRANSITIONS: dict[str, list[str]] = {
    "open": ["triage", "cancelled"],
    "triage": ["in_analysis", "cancelled"],
    "in_analysis": ["actioning", "triage", "cancelled"],
    "actioning": ["monitoring", "in_analysis", "cancelled"],
    "monitoring": ["closed", "actioning"],
    # closed / cancelled are terminal
}


# ═══════════════════════════════════════════════════════════════════
# Case CRUD (B05.1)
# ═══════════════════════════════════════════════════════════════════

async def _generate_case_no(db: AsyncSession) -> str:
    """Generate unique case number: CASE-YYYY-NNNN."""
    year = datetime.now(timezone.utc).year
    prefix = f"CASE-{year}-"
    result = await db.execute(
        select(func.count())
        .select_from(RiskCase)
        .where(RiskCase.case_no.like(f"{prefix}%"))
    )
    count = (result.scalar() or 0) + 1
    return f"{prefix}{count:04d}"


async def create_case(
    db: AsyncSession, data: CaseCreate, created_by_user_id: uuid.UUID
) -> RiskCase:
    _validate_priority(data.priority)
    _validate_severity(data.severity)
    if data.case_type not in VALID_CASE_TYPES:
        raise AppException(422, "INVALID_CASE_TYPE", f"case_type phải là: {', '.join(sorted(VALID_CASE_TYPES))}")

    case_no = await _generate_case_no(db)

    case = RiskCase(
        farm_id=data.farm_id,
        area_id=data.area_id,
        case_no=case_no,
        case_type=data.case_type,
        title=data.title,
        summary=data.summary,
        source_assessment_id=data.source_assessment_id,
        source_killer_event_id=data.source_killer_event_id,
        source_scar_id=data.source_scar_id,
        priority=data.priority,
        severity=data.severity,
        current_status="open",
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)

    # Add creator as owner participant
    participant = CaseParticipant(
        case_id=case.id,
        user_id=created_by_user_id,
        role_in_case="owner",
    )
    db.add(participant)

    # B05.9: If case is from killer event, transition event to under_review
    if data.source_killer_event_id:
        await _link_killer_event(db, data.source_killer_event_id)

    await db.flush()
    await db.commit()
    return await get_case(db, case.id)


async def list_cases(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    priority: str | None = None,
    current_status: str | None = None,
    case_type: str | None = None,
    assigned_expert_user_id: uuid.UUID | None = None,
    queue_my: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[RiskCase], int]:
    base = select(RiskCase).where(RiskCase.archived_at.is_(None))
    count_q = select(func.count()).select_from(RiskCase).where(RiskCase.archived_at.is_(None))

    if farm_id:
        base = base.where(RiskCase.farm_id == farm_id)
        count_q = count_q.where(RiskCase.farm_id == farm_id)
    if priority:
        base = base.where(RiskCase.priority == priority)
        count_q = count_q.where(RiskCase.priority == priority)
    if current_status:
        base = base.where(RiskCase.current_status == current_status)
        count_q = count_q.where(RiskCase.current_status == current_status)
    if case_type:
        base = base.where(RiskCase.case_type == case_type)
        count_q = count_q.where(RiskCase.case_type == case_type)
    if assigned_expert_user_id:
        base = base.where(RiskCase.assigned_expert_user_id == assigned_expert_user_id)
        count_q = count_q.where(RiskCase.assigned_expert_user_id == assigned_expert_user_id)
    if queue_my:
        base = base.where(RiskCase.assigned_expert_user_id == queue_my)
        count_q = count_q.where(RiskCase.assigned_expert_user_id == queue_my)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(RiskCase.priority, RiskCase.opened_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_case(db: AsyncSession, case_id: uuid.UUID) -> RiskCase:
    result = await db.execute(
        select(RiskCase)
        .options(
            selectinload(RiskCase.participants),
            selectinload(RiskCase.rca_records).selectinload(RcaRecord.factors),
        )
        .where(RiskCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("Risk case not found.")
    return case


async def update_case(
    db: AsyncSession, case_id: uuid.UUID, data: CaseUpdate
) -> RiskCase:
    case = await get_case(db, case_id)
    check_version(case.version, data.version)

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})
    if "priority" in update_data:
        _validate_priority(update_data["priority"])
    if "severity" in update_data:
        _validate_severity(update_data["severity"])

    for key, value in update_data.items():
        setattr(case, key, value)
    case.version = apply_version_update(case.version)
    await db.flush()
    await db.refresh(case)
    await db.commit()
    return await get_case(db, case.id)


# ═══════════════════════════════════════════════════════════════════
# Case Queue (B05.2)
# ═══════════════════════════════════════════════════════════════════

async def get_queue_review(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[RiskCase], int]:
    """Expert review queue: non-closed/cancelled cases sorted by SLA urgency then priority."""
    active_statuses = ("open", "triage", "in_analysis", "actioning", "monitoring")
    base = select(RiskCase).where(
        RiskCase.archived_at.is_(None),
        RiskCase.current_status.in_(active_statuses),
    )
    count_q = select(func.count()).select_from(RiskCase).where(
        RiskCase.archived_at.is_(None),
        RiskCase.current_status.in_(active_statuses),
    )

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    # Sort: priority ASC (P0 first), then first_response_due_at ASC (most urgent first)
    result = await db.execute(
        base.order_by(
            RiskCase.priority,
            RiskCase.first_response_due_at.asc().nulls_last(),
            RiskCase.opened_at.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


# ═══════════════════════════════════════════════════════════════════
# Case State Machine (B05.4)
# ═══════════════════════════════════════════════════════════════════

async def change_status(
    db: AsyncSession, case_id: uuid.UUID, data: ChangeStatusRequest
) -> RiskCase:
    case = await get_case(db, case_id)
    check_version(case.version, data.version)
    _validate_transition(case.current_status, data.target_status)

    case.current_status = data.target_status
    if data.target_status in ("closed", "cancelled"):
        case.closed_at = datetime.now(timezone.utc)
    case.version = apply_version_update(case.version)
    await db.flush()
    await db.refresh(case)
    await db.commit()
    return await get_case(db, case.id)


# ═══════════════════════════════════════════════════════════════════
# Assign Expert (B05.5)
# ═══════════════════════════════════════════════════════════════════

async def assign_expert(
    db: AsyncSession, case_id: uuid.UUID, expert_user_id: uuid.UUID
) -> RiskCase:
    from app.auth.models import AppPermission, AppUser, RolePermission, UserRole

    case = await get_case(db, case_id)

    # Validate expert user exists and is active
    result = await db.execute(
        select(AppUser).where(AppUser.id == expert_user_id, AppUser.status == "active")
    )
    expert = result.scalar_one_or_none()
    if not expert:
        raise NotFoundException("Expert user not found or inactive.")

    # Validate user has expert-level permission (RCA_WRITE implies expert role)
    perm_check = await db.execute(
        select(func.count())
        .select_from(UserRole)
        .join(RolePermission, RolePermission.role_id == UserRole.role_id)
        .join(AppPermission, AppPermission.id == RolePermission.permission_id)
        .where(UserRole.user_id == expert_user_id, AppPermission.code == "RCA_WRITE")
    )
    if (perm_check.scalar() or 0) == 0:
        raise AppException(422, "NOT_EXPERT", "User không có quyền chuyên gia (RCA_WRITE).")

    case.assigned_expert_user_id = expert_user_id
    case.version = apply_version_update(case.version)
    await db.flush()

    # Add expert as reviewer participant if not already present
    existing = await db.execute(
        select(CaseParticipant).where(
            CaseParticipant.case_id == case.id,
            CaseParticipant.user_id == expert_user_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(CaseParticipant(
            case_id=case.id,
            user_id=expert_user_id,
            role_in_case="reviewer",
        ))
        await db.flush()

    await db.refresh(case)
    await db.commit()
    return await get_case(db, case.id)


# ═══════════════════════════════════════════════════════════════════
# Timeline (B05.3)
# ═══════════════════════════════════════════════════════════════════

async def get_timeline(db: AsyncSession, case_id: uuid.UUID) -> list[TimelineEntry]:
    """Build chronological timeline for a case from related entities."""
    case = await get_case(db, case_id)
    entries: list[TimelineEntry] = []

    # Case opened
    entries.append(TimelineEntry(
        event_type="case_opened",
        occurred_at=case.opened_at,
        detail=f"Case {case.case_no} opened — {case.title}",
    ))

    # Case closed
    if case.closed_at:
        entries.append(TimelineEntry(
            event_type="case_closed",
            occurred_at=case.closed_at,
            detail=f"Case {case.case_no} {case.current_status}",
        ))

    # RCA records
    for rca in case.rca_records:
        entries.append(TimelineEntry(
            event_type="rca_created",
            occurred_at=rca.analyzed_at,
            detail=f"RCA ({rca.method}): {rca.problem_statement[:100]}",
        ))
        if rca.approved_at:
            entries.append(TimelineEntry(
                event_type="rca_approved",
                occurred_at=rca.approved_at,
                detail=f"RCA ({rca.method}) approved",
            ))

    # Source killer event if any
    if case.source_killer_event_id:
        from app.killer_metrics.models import KillerMetricEvent
        result = await db.execute(
            select(KillerMetricEvent).where(KillerMetricEvent.id == case.source_killer_event_id)
        )
        km_event = result.scalar_one_or_none()
        if km_event:
            entries.append(TimelineEntry(
                event_type="killer_event",
                occurred_at=km_event.event_at,
                detail=f"Killer metric event: {km_event.summary[:100]}",
            ))

    entries.sort(key=lambda e: e.occurred_at)
    return entries


# ═══════════════════════════════════════════════════════════════════
# RCA Record CRUD (B05.6)
# ═══════════════════════════════════════════════════════════════════

async def list_rca_records(db: AsyncSession, case_id: uuid.UUID) -> list[RcaRecord]:
    # Validate case exists
    await get_case(db, case_id)
    result = await db.execute(
        select(RcaRecord)
        .options(selectinload(RcaRecord.factors))
        .where(RcaRecord.case_id == case_id)
        .order_by(RcaRecord.analyzed_at.desc())
    )
    return list(result.scalars().all())


async def create_rca_record(
    db: AsyncSession, case_id: uuid.UUID, data: RcaRecordCreate, user_id: uuid.UUID
) -> RcaRecord:
    await get_case(db, case_id)
    _validate_rca_method(data.method)
    _validate_confidence(data.conclusion_confidence)

    rca = RcaRecord(
        case_id=case_id,
        method=data.method,
        problem_statement=data.problem_statement,
        impact_scope=data.impact_scope,
        direct_cause=data.direct_cause,
        system_cause=data.system_cause,
        behavioral_cause=data.behavioral_cause,
        structural_cause=data.structural_cause,
        monitoring_cause=data.monitoring_cause,
        external_factor=data.external_factor,
        conclusion_confidence=data.conclusion_confidence,
        analyzed_by_user_id=user_id,
    )
    db.add(rca)
    await db.flush()
    await db.refresh(rca)
    await db.commit()
    return await get_rca_record(db, rca.id)


async def get_rca_record(db: AsyncSession, rca_id: uuid.UUID) -> RcaRecord:
    result = await db.execute(
        select(RcaRecord)
        .options(selectinload(RcaRecord.factors))
        .where(RcaRecord.id == rca_id)
    )
    rca = result.scalar_one_or_none()
    if not rca:
        raise NotFoundException("RCA record not found.")
    return rca


async def update_rca_record(
    db: AsyncSession, rca_id: uuid.UUID, data: RcaRecordUpdate
) -> RcaRecord:
    rca = await get_rca_record(db, rca_id)
    if rca.approved_at:
        raise AppException(409, "ALREADY_APPROVED", "Không thể sửa RCA đã được phê duyệt.")

    update_data = data.model_dump(exclude_unset=True)
    if "method" in update_data:
        _validate_rca_method(update_data["method"])
    if "conclusion_confidence" in update_data:
        _validate_confidence(update_data["conclusion_confidence"])

    for key, value in update_data.items():
        setattr(rca, key, value)
    await db.flush()
    await db.refresh(rca)
    await db.commit()
    return await get_rca_record(db, rca.id)


# ═══════════════════════════════════════════════════════════════════
# RCA Approve (B05.8)
# ═══════════════════════════════════════════════════════════════════

async def approve_rca_record(
    db: AsyncSession, rca_id: uuid.UUID, approved_by_user_id: uuid.UUID
) -> RcaRecord:
    rca = await get_rca_record(db, rca_id)
    if rca.approved_at:
        raise AppException(409, "ALREADY_APPROVED", "RCA đã được phê duyệt trước đó.")

    rca.approved_by_user_id = approved_by_user_id
    rca.approved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(rca)
    await db.commit()
    return await get_rca_record(db, rca.id)


# ═══════════════════════════════════════════════════════════════════
# RCA Factors (B05.7)
# ═══════════════════════════════════════════════════════════════════

async def create_rca_factor(
    db: AsyncSession, rca_id: uuid.UUID, data: RcaFactorCreate
) -> RcaFactor:
    rca = await get_rca_record(db, rca_id)
    if rca.approved_at:
        raise AppException(409, "ALREADY_APPROVED", "Không thể thêm factor vào RCA đã phê duyệt.")
    _validate_factor_group(data.factor_group)
    _validate_confidence(data.confidence_level)

    factor = RcaFactor(
        rca_record_id=rca_id,
        factor_group=data.factor_group,
        factor_text=data.factor_text,
        confidence_level=data.confidence_level,
        is_primary=data.is_primary,
    )
    db.add(factor)
    await db.flush()
    await db.refresh(factor)
    await db.commit()
    return factor


async def get_rca_factor(db: AsyncSession, factor_id: uuid.UUID) -> RcaFactor:
    result = await db.execute(
        select(RcaFactor).where(RcaFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()
    if not factor:
        raise NotFoundException("RCA factor not found.")
    return factor


async def update_rca_factor(
    db: AsyncSession, factor_id: uuid.UUID, data: RcaFactorUpdate
) -> RcaFactor:
    factor = await get_rca_factor(db, factor_id)

    # Check parent RCA not approved
    rca = await get_rca_record(db, factor.rca_record_id)
    if rca.approved_at:
        raise AppException(409, "ALREADY_APPROVED", "Không thể sửa factor khi RCA đã phê duyệt.")

    update_data = data.model_dump(exclude_unset=True)
    if "factor_group" in update_data:
        _validate_factor_group(update_data["factor_group"])
    if "confidence_level" in update_data:
        _validate_confidence(update_data["confidence_level"])

    for key, value in update_data.items():
        setattr(factor, key, value)
    await db.flush()
    await db.refresh(factor)
    await db.commit()
    return factor


async def delete_rca_factor(db: AsyncSession, factor_id: uuid.UUID) -> None:
    factor = await get_rca_factor(db, factor_id)

    # Check parent RCA not approved
    rca = await get_rca_record(db, factor.rca_record_id)
    if rca.approved_at:
        raise AppException(409, "ALREADY_APPROVED", "Không thể xóa factor khi RCA đã phê duyệt.")

    await db.delete(factor)
    await db.flush()
    await db.commit()


# ═══════════════════════════════════════════════════════════════════
# B05.9: Case → Killer Event link
# ═══════════════════════════════════════════════════════════════════

async def _link_killer_event(db: AsyncSession, killer_event_id: uuid.UUID) -> None:
    """Transition killer event to under_review when case is created from it."""
    from app.killer_metrics.models import KillerMetricEvent

    result = await db.execute(
        select(KillerMetricEvent).where(KillerMetricEvent.id == killer_event_id)
    )
    event = result.scalar_one_or_none()
    if event and event.status == "open":
        event.status = "under_review"
        event.version = event.version + 1
        await db.flush()


# ═══════════════════════════════════════════════════════════════════
# Validation helpers
# ═══════════════════════════════════════════════════════════════════

def _validate_priority(value: str) -> None:
    if value not in VALID_PRIORITIES:
        raise AppException(422, "INVALID_PRIORITY", f"priority phải là: {', '.join(sorted(VALID_PRIORITIES))}")


def _validate_severity(value: str) -> None:
    if value not in VALID_SEVERITIES:
        raise AppException(422, "INVALID_SEVERITY", f"severity phải là: {', '.join(sorted(VALID_SEVERITIES))}")


def _validate_rca_method(value: str) -> None:
    if value not in VALID_RCA_METHODS:
        raise AppException(422, "INVALID_RCA_METHOD", f"method phải là: {', '.join(sorted(VALID_RCA_METHODS))}")


def _validate_confidence(value: str) -> None:
    if value not in VALID_CONFIDENCE:
        raise AppException(422, "INVALID_CONFIDENCE", f"confidence phải là: {', '.join(sorted(VALID_CONFIDENCE))}")


def _validate_factor_group(value: str) -> None:
    if value not in VALID_FACTOR_GROUPS:
        raise AppException(422, "INVALID_FACTOR_GROUP", f"factor_group phải là: {', '.join(sorted(VALID_FACTOR_GROUPS))}")


def _validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ConflictException(
            message=f"Không thể chuyển trạng thái từ '{current}' sang '{target}'. "
            f"Cho phép: {', '.join(allowed) if allowed else 'không có (terminal)'}."
        )
