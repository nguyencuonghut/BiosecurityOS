"""Business logic for Lesson Learned module (Sprint 08)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.lessons.models import LessonLearned, LessonReference, SimilarityTag
from app.lessons.schemas import (
    LessonCreate,
    LessonUpdate,
    ReferenceCreate,
    TagCreate,
    VALID_CONFIDENCE_LEVELS,
    VALID_STATUSES,
    VALID_REFERENCE_TYPES,
    VALID_TAG_TYPES,
)
from app.shared.exceptions import AppException, NotFoundException


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

async def _generate_lesson_no(db: AsyncSession) -> str:
    """Generate unique lesson number: LL-YYYY-NNNN."""
    year = datetime.now(timezone.utc).year
    prefix = f"LL-{year}-"
    result = await db.execute(
        select(func.count())
        .select_from(LessonLearned)
        .where(LessonLearned.lesson_no.like(f"{prefix}%"))
    )
    count = (result.scalar() or 0) + 1
    return f"{prefix}{count:04d}"


def _lesson_load_options():
    return [selectinload(LessonLearned.references), selectinload(LessonLearned.tags)]


# ═══════════════════════════════════════════════════════════════════
# CRUD (B08.1)
# ═══════════════════════════════════════════════════════════════════

async def list_lessons(
    db: AsyncSession,
    *,
    farm_type: str | None = None,
    issue_type: str | None = None,
    confidence_level: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[LessonLearned], int]:
    base = select(LessonLearned).where(LessonLearned.archived_at.is_(None))
    count_q = select(func.count()).select_from(LessonLearned).where(LessonLearned.archived_at.is_(None))

    if confidence_level:
        base = base.where(LessonLearned.confidence_level == confidence_level)
        count_q = count_q.where(LessonLearned.confidence_level == confidence_level)
    if status:
        base = base.where(LessonLearned.status == status)
        count_q = count_q.where(LessonLearned.status == status)

    # Tag-based filters: join similarity_tag
    tag_filters = []
    if farm_type:
        tag_filters.append(("farm_type", farm_type))
    if issue_type:
        tag_filters.append(("issue_type", issue_type))
    if tag:
        # generic tag search (any tag_value matches)
        tag_filters.append((None, tag))

    if tag_filters:
        for tag_type, tag_value in tag_filters:
            tag_sub = select(SimilarityTag.lesson_id)
            if tag_type:
                tag_sub = tag_sub.where(
                    SimilarityTag.tag_type == tag_type,
                    SimilarityTag.tag_value == tag_value,
                )
            else:
                tag_sub = tag_sub.where(SimilarityTag.tag_value == tag_value)
            base = base.where(LessonLearned.id.in_(tag_sub))
            count_q = count_q.where(LessonLearned.id.in_(tag_sub))

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(LessonLearned.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_lesson(db: AsyncSession, lesson_id: uuid.UUID) -> LessonLearned:
    result = await db.execute(
        select(LessonLearned)
        .options(*_lesson_load_options())
        .where(LessonLearned.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise NotFoundException("Lesson learned not found.")
    return lesson


async def create_lesson(
    db: AsyncSession, data: LessonCreate
) -> LessonLearned:
    if data.confidence_level not in VALID_CONFIDENCE_LEVELS:
        raise AppException(
            422, "INVALID_CONFIDENCE_LEVEL",
            f"confidence_level phải là: {', '.join(VALID_CONFIDENCE_LEVELS)}"
        )

    lesson_no = await _generate_lesson_no(db)

    lesson = LessonLearned(
        lesson_no=lesson_no,
        title=data.title,
        problem_context=data.problem_context,
        root_cause_summary=data.root_cause_summary,
        action_summary=data.action_summary,
        outcome_summary=data.outcome_summary,
        recurrence_observed=data.recurrence_observed,
        applicability_scope=data.applicability_scope,
        confidence_level=data.confidence_level,
        status="draft",
    )
    db.add(lesson)
    await db.flush()
    await db.commit()
    return await get_lesson(db, lesson.id)


async def update_lesson(
    db: AsyncSession, lesson_id: uuid.UUID, data: LessonUpdate
) -> LessonLearned:
    lesson = await get_lesson(db, lesson_id)

    updates = data.model_dump(exclude_unset=True)

    if "confidence_level" in updates and updates["confidence_level"] not in VALID_CONFIDENCE_LEVELS:
        raise AppException(
            422, "INVALID_CONFIDENCE_LEVEL",
            f"confidence_level phải là: {', '.join(VALID_CONFIDENCE_LEVELS)}"
        )
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise AppException(
            422, "INVALID_STATUS",
            f"status phải là: {', '.join(VALID_STATUSES)}"
        )

    for field, value in updates.items():
        setattr(lesson, field, value)

    await db.flush()
    await db.commit()
    return await get_lesson(db, lesson_id)


# ═══════════════════════════════════════════════════════════════════
# Validate (B08.2)
# ═══════════════════════════════════════════════════════════════════

async def validate_lesson(
    db: AsyncSession, lesson_id: uuid.UUID, confirmed_by_user_id: uuid.UUID
) -> LessonLearned:
    lesson = await get_lesson(db, lesson_id)

    if lesson.status == "validated":
        raise AppException(409, "ALREADY_VALIDATED", "Lesson đã được xác nhận.")

    # Must have at least 1 reference (BR-05 requirement)
    ref_count = (await db.execute(
        select(func.count()).select_from(LessonReference)
        .where(LessonReference.lesson_id == lesson_id)
    )).scalar() or 0
    if ref_count == 0:
        raise AppException(
            422, "MISSING_REFERENCE",
            "Không thể xác nhận lesson chưa có reference nào."
        )

    lesson.status = "validated"
    lesson.confidence_level = "confirmed"
    lesson.confirmed_by_user_id = confirmed_by_user_id
    lesson.confirmed_at = datetime.now(timezone.utc)

    await db.flush()
    await db.commit()
    return await get_lesson(db, lesson_id)


# ═══════════════════════════════════════════════════════════════════
# References (B08.3)
# ═══════════════════════════════════════════════════════════════════

async def add_reference(
    db: AsyncSession, lesson_id: uuid.UUID, data: ReferenceCreate
) -> LessonReference:
    await get_lesson(db, lesson_id)

    if data.reference_type not in VALID_REFERENCE_TYPES:
        raise AppException(
            422, "INVALID_REFERENCE_TYPE",
            f"reference_type phải là: {', '.join(VALID_REFERENCE_TYPES)}"
        )

    # Validate referenced object exists (BR-08)
    await _validate_referenced_object(db, data.reference_type, data.reference_id)

    # Check duplicate
    dup = await db.execute(
        select(LessonReference).where(
            LessonReference.lesson_id == lesson_id,
            LessonReference.reference_type == data.reference_type,
            LessonReference.reference_id == data.reference_id,
        )
    )
    if dup.scalar_one_or_none():
        raise AppException(409, "DUPLICATE_REFERENCE", "Reference này đã tồn tại.")

    ref = LessonReference(
        lesson_id=lesson_id,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        contribution_note=data.contribution_note,
    )
    db.add(ref)
    await db.flush()
    await db.refresh(ref)
    await db.commit()
    return ref


async def _validate_referenced_object(
    db: AsyncSession, ref_type: str, ref_id: uuid.UUID
) -> None:
    """Validate that the referenced object exists (BR-08)."""
    if ref_type == "scar":
        from app.scars.models import ScarRecord
        result = await db.execute(select(ScarRecord).where(ScarRecord.id == ref_id))
    elif ref_type == "case":
        from app.cases.models import RiskCase
        result = await db.execute(select(RiskCase).where(RiskCase.id == ref_id))
    elif ref_type == "task":
        from app.tasks.models import CorrectiveTask
        result = await db.execute(select(CorrectiveTask).where(CorrectiveTask.id == ref_id))
    elif ref_type == "assessment":
        from app.assessments.models import Assessment
        result = await db.execute(select(Assessment).where(Assessment.id == ref_id))
    else:
        raise AppException(
            422, "INVALID_REFERENCE_TYPE",
            f"Loại reference không hợp lệ: {ref_type}"
        )

    if not result.scalar_one_or_none():
        raise NotFoundException(
            f"Đối tượng {ref_type} với id {ref_id} không tồn tại."
        )


# ═══════════════════════════════════════════════════════════════════
# Tags (B08.4)
# ═══════════════════════════════════════════════════════════════════

async def add_tag(
    db: AsyncSession, lesson_id: uuid.UUID, data: TagCreate
) -> SimilarityTag:
    await get_lesson(db, lesson_id)

    if data.tag_type not in VALID_TAG_TYPES:
        raise AppException(
            422, "INVALID_TAG_TYPE",
            f"tag_type phải là: {', '.join(VALID_TAG_TYPES)}"
        )

    # Check duplicate
    dup = await db.execute(
        select(SimilarityTag).where(
            SimilarityTag.lesson_id == lesson_id,
            SimilarityTag.tag_type == data.tag_type,
            SimilarityTag.tag_value == data.tag_value,
        )
    )
    if dup.scalar_one_or_none():
        raise AppException(409, "DUPLICATE_TAG", "Tag này đã tồn tại cho lesson.")

    tag = SimilarityTag(
        lesson_id=lesson_id,
        tag_type=data.tag_type,
        tag_value=data.tag_value,
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    await db.commit()
    return tag


# ═══════════════════════════════════════════════════════════════════
# Similar Search (B08.5)
# ═══════════════════════════════════════════════════════════════════

async def search_similar(
    db: AsyncSession,
    *,
    farm_type: str | None = None,
    ownership_type: str | None = None,
    issue_type: str | None = None,
    area_type: str | None = None,
    route_type: str | None = None,
    season: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[LessonLearned], int]:
    """Search lessons by similarity tags. Only returns validated lessons by default."""
    base = (
        select(LessonLearned)
        .where(LessonLearned.archived_at.is_(None))
        .where(LessonLearned.status == "validated")
    )
    count_q = (
        select(func.count()).select_from(LessonLearned)
        .where(LessonLearned.archived_at.is_(None))
        .where(LessonLearned.status == "validated")
    )

    # Build tag filters — each narrows the result set
    tag_criteria = []
    if farm_type:
        tag_criteria.append(("farm_type", farm_type))
    if ownership_type:
        tag_criteria.append(("ownership_type", ownership_type))
    if issue_type:
        tag_criteria.append(("issue_type", issue_type))
    if area_type:
        tag_criteria.append(("other", area_type))  # area_type stored as 'other'
    if route_type:
        tag_criteria.append(("route_type", route_type))
    if season:
        tag_criteria.append(("season", season))

    for tag_type, tag_value in tag_criteria:
        sub = select(SimilarityTag.lesson_id).where(
            SimilarityTag.tag_type == tag_type,
            SimilarityTag.tag_value == tag_value,
        )
        base = base.where(LessonLearned.id.in_(sub))
        count_q = count_q.where(LessonLearned.id.in_(sub))

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.options(*_lesson_load_options())
        .order_by(LessonLearned.confirmed_at.desc().nulls_last())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total
