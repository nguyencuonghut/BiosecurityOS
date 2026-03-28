"""Assessment service — CRUD, bulk upsert, submit, score calc, spider chart, state machine."""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assessments.models import Assessment, AssessmentAttachment, AssessmentItemResult, AssessmentStatus
from app.assessments.schemas import (
    AssessmentAttachmentCreate,
    AssessmentCreate,
    AssessmentUpdate,
    BulkUpsertRequest,
)
from app.auth.models import AppUser, Farm
from app.scorecards.models import ScorecardItem, ScorecardSection, ScorecardTemplate
from app.shared.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)

# ── Valid state transitions ─────────────────────────────────────
VALID_TRANSITIONS: dict[AssessmentStatus, list[AssessmentStatus]] = {
    AssessmentStatus.DRAFT:     [AssessmentStatus.SUBMITTED],
    AssessmentStatus.SUBMITTED: [AssessmentStatus.REVIEWED],
    AssessmentStatus.REVIEWED:  [AssessmentStatus.LOCKED],
    AssessmentStatus.LOCKED:    [],
}

# ── Section type → score field mapping ──────────────────────────
SECTION_TYPE_SCORE_FIELD = {
    "hardware": "hardware_score",
    "software": "process_score",  # "software" section maps to process_score
    "behavior": "behavior_score",
    "monitoring": "monitoring_score",
}

SPIDER_AXES = [
    ("HARDWARE", "Hạ tầng", "hardware_score"),
    ("PROCESS", "Quy trình", "process_score"),
    ("BEHAVIOR", "Hành vi", "behavior_score"),
    ("MONITORING", "Giám sát", "monitoring_score"),
]


# ── Helpers ─────────────────────────────────────────────────────

async def _get_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> Assessment:
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise NotFoundException(f"Assessment {assessment_id} không tồn tại.")
    return obj


async def _get_assessment_detail(db: AsyncSession, assessment_id: uuid.UUID) -> Assessment:
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(
            selectinload(Assessment.item_results),
            selectinload(Assessment.attachments),
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise NotFoundException(f"Assessment {assessment_id} không tồn tại.")
    return obj


def _validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ValidationException(
            f"Không thể chuyển trạng thái từ '{current}' sang '{target}'. "
            f"Trạng thái hợp lệ: {allowed or 'không có'}."
        )


# ── Assessment CRUD ─────────────────────────────────────────────

async def list_assessments(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    assessment_type: str | None = None,
    status: AssessmentStatus | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Assessment], int]:
    query = select(Assessment)
    count_q = select(func.count()).select_from(Assessment)

    if farm_id:
        query = query.where(Assessment.farm_id == farm_id)
        count_q = count_q.where(Assessment.farm_id == farm_id)
    if assessment_type:
        query = query.where(Assessment.assessment_type == assessment_type)
        count_q = count_q.where(Assessment.assessment_type == assessment_type)
    if status:
        query = query.where(Assessment.status == status)
        count_q = count_q.where(Assessment.status == status)
    if date_from:
        query = query.where(Assessment.assessment_date >= date_from)
        count_q = count_q.where(Assessment.assessment_date >= date_from)
    if date_to:
        query = query.where(Assessment.assessment_date <= date_to)
        count_q = count_q.where(Assessment.assessment_date <= date_to)

    total = (await db.execute(count_q)).scalar() or 0
    query = (
        query.order_by(Assessment.assessment_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_assessment(
    db: AsyncSession, data: AssessmentCreate, user: AppUser
) -> Assessment:
    # Validate farm exists
    farm_result = await db.execute(select(Farm).where(Farm.id == data.farm_id))
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise NotFoundException(f"Farm {data.farm_id} không tồn tại.")

    # Validate template exists and is active (BR-07: snapshot template at creation)
    tmpl_result = await db.execute(
        select(ScorecardTemplate).where(ScorecardTemplate.id == data.template_id)
    )
    tmpl = tmpl_result.scalar_one_or_none()
    if not tmpl:
        raise NotFoundException(f"Template {data.template_id} không tồn tại.")
    if tmpl.status != "active":
        raise ValidationException("Chỉ có thể tạo assessment từ template đang active.")

    assessment = Assessment(
        farm_id=data.farm_id,
        template_id=data.template_id,
        assessment_type=data.assessment_type,
        assessment_date=data.assessment_date or func.now(),
        performed_by_user_id=user.id,
        performed_by_name_snapshot=user.full_name or user.username,
        status=AssessmentStatus.DRAFT,
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)
    return assessment


async def get_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> Assessment:
    return await _get_assessment_detail(db, assessment_id)


async def update_assessment(
    db: AsyncSession, assessment_id: uuid.UUID, data: AssessmentUpdate
) -> Assessment:
    obj = await _get_assessment(db, assessment_id)
    if obj.status != AssessmentStatus.DRAFT:
        raise ValidationException("Chỉ có thể sửa assessment ở trạng thái draft.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


# ── Bulk Upsert Item Results (B03.4) ───────────────────────────

async def bulk_upsert_item_results(
    db: AsyncSession, assessment_id: uuid.UUID, data: BulkUpsertRequest
) -> list[AssessmentItemResult]:
    obj = await _get_assessment(db, assessment_id)
    if obj.status != AssessmentStatus.DRAFT:
        raise ValidationException("Chỉ có thể cập nhật kết quả khi assessment ở trạng thái draft.")

    # Fetch template sections → items to validate item belongs to template
    tmpl_result = await db.execute(
        select(ScorecardTemplate)
        .where(ScorecardTemplate.id == obj.template_id)
        .options(
            selectinload(ScorecardTemplate.sections).selectinload(ScorecardSection.items)
        )
    )
    tmpl = tmpl_result.scalar_one_or_none()
    if not tmpl:
        raise NotFoundException("Template liên kết không tồn tại.")

    valid_item_ids = set()
    for section in tmpl.sections:
        for item in section.items:
            valid_item_ids.add(item.id)

    # Validate all submitted items belong to the template
    for item_in in data.items:
        if item_in.scorecard_item_id not in valid_item_ids:
            raise ValidationException(
                f"Item {item_in.scorecard_item_id} không thuộc template của assessment này."
            )

    # Load existing results for this assessment
    existing_result = await db.execute(
        select(AssessmentItemResult).where(AssessmentItemResult.assessment_id == assessment_id)
    )
    existing_map: dict[uuid.UUID, AssessmentItemResult] = {
        r.scorecard_item_id: r for r in existing_result.scalars().all()
    }

    results = []
    for item_in in data.items:
        if item_in.scorecard_item_id in existing_map:
            # Update existing
            existing = existing_map[item_in.scorecard_item_id]
            existing.response_value_text = item_in.response_value_text
            existing.response_value_numeric = item_in.response_value_numeric
            existing.awarded_score = item_in.awarded_score
            existing.is_non_compliant = item_in.is_non_compliant
            existing.note = item_in.note
            existing.area_id = item_in.area_id
            existing.evidence_required = item_in.evidence_required
            results.append(existing)
        else:
            # Insert new
            new_result = AssessmentItemResult(
                assessment_id=assessment_id,
                **item_in.model_dump(),
            )
            db.add(new_result)
            results.append(new_result)

    await db.flush()
    return results


# ── Score Calculation (B03.6) ───────────────────────────────────

async def calculate_scores(db: AsyncSession, assessment_id: uuid.UUID) -> Assessment:
    """Calculate overall + 4 axis scores from item results weighted by section/item weights."""
    obj = await _get_assessment(db, assessment_id)

    # Load template with sections → items
    tmpl_result = await db.execute(
        select(ScorecardTemplate)
        .where(ScorecardTemplate.id == obj.template_id)
        .options(
            selectinload(ScorecardTemplate.sections).selectinload(ScorecardSection.items)
        )
    )
    tmpl = tmpl_result.scalar_one_or_none()
    if not tmpl:
        raise NotFoundException("Template liên kết không tồn tại.")

    # Load item results
    results_q = await db.execute(
        select(AssessmentItemResult).where(AssessmentItemResult.assessment_id == assessment_id)
    )
    result_map: dict[uuid.UUID, AssessmentItemResult] = {
        r.scorecard_item_id: r for r in results_q.scalars().all()
    }

    # Calculate per-section scores
    section_scores: dict[str, Decimal] = {}  # section_type → weighted score (0-100)
    total_section_weight = Decimal("0")

    for section in tmpl.sections:
        if not section.items:
            continue

        # Calculate section score: sum(item.awarded_score * item.weight) / sum(item.max_score * item.weight) * 100
        weighted_awarded = Decimal("0")
        weighted_max = Decimal("0")

        for item in section.items:
            result = result_map.get(item.id)
            awarded = result.awarded_score if result else Decimal("0")
            weighted_awarded += awarded * item.weight
            weighted_max += item.max_score * item.weight

        if weighted_max > 0:
            score = (weighted_awarded / weighted_max * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            score = Decimal("0")

        # Accumulate by section_type
        st = section.section_type
        if st in section_scores:
            # Multiple sections of same type — weighted average
            # This is a simplification; we take the last one's weight
            pass
        section_scores[st] = score
        total_section_weight += section.weight

    # Map section_type scores to assessment fields
    for section_type, field_name in SECTION_TYPE_SCORE_FIELD.items():
        score_val = section_scores.get(section_type)
        setattr(obj, field_name, score_val)

    # Calculate overall_score: weighted average of section scores
    if total_section_weight > 0:
        overall = Decimal("0")
        for section in tmpl.sections:
            st = section.section_type
            s_score = section_scores.get(st, Decimal("0"))
            overall += s_score * section.weight
        overall = (overall / total_section_weight).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        obj.overall_score = overall
    else:
        obj.overall_score = Decimal("0")

    await db.flush()
    return obj


# ── Submit Assessment (B03.5) ───────────────────────────────────

async def submit_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> Assessment:
    """Transition draft → submitted and calculate scores."""
    obj = await _get_assessment(db, assessment_id)
    _validate_transition(obj.status, AssessmentStatus.SUBMITTED)

    # Calculate scores before submitting
    obj = await calculate_scores(db, assessment_id)
    obj.status = AssessmentStatus.SUBMITTED
    obj.version += 1
    await db.flush()
    await db.refresh(obj)
    return obj


# ── State Machine Transitions (B03.8) ──────────────────────────

async def change_status(
    db: AsyncSession,
    assessment_id: uuid.UUID,
    target_status: AssessmentStatus,
    expected_version: int,
) -> Assessment:
    """Generic state transition with optimistic lock check."""
    obj = await _get_assessment(db, assessment_id)

    if obj.version != expected_version:
        raise ConflictException(
            f"Version conflict: expected {expected_version}, actual {obj.version}."
        )

    _validate_transition(obj.status, target_status)
    obj.status = target_status
    obj.version += 1
    await db.flush()
    await db.refresh(obj)
    return obj


# ── Spider Chart (B03.7) ───────────────────────────────────────

async def get_spider_chart(db: AsyncSession, assessment_id: uuid.UUID) -> dict:
    obj = await _get_assessment(db, assessment_id)
    axes = []
    for code, label, field in SPIDER_AXES:
        score = getattr(obj, field, None)
        axes.append({"code": code, "label": label, "score": float(score) if score is not None else None})
    return {
        "farm_id": str(obj.farm_id),
        "assessment_id": str(obj.id),
        "axes": axes,
    }


# ── Attachment ──────────────────────────────────────────────────

async def add_attachment(
    db: AsyncSession, assessment_id: uuid.UUID, data: AssessmentAttachmentCreate
) -> AssessmentAttachment:
    await _get_assessment(db, assessment_id)
    att = AssessmentAttachment(assessment_id=assessment_id, **data.model_dump())
    db.add(att)
    await db.flush()
    await db.refresh(att)
    return att
