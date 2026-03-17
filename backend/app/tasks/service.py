"""Service layer for Corrective Task module (Sprint 06).

Covers: B06.1–B06.6, B06.12 — Task CRUD, state machine, assignees, reviews, comments.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.tasks.models import CorrectiveTask, TaskAssignee, TaskAttachment, TaskComment, TaskReview
from app.tasks.schemas import (
    ChangeTaskStatusRequest,
    TaskAssigneeInput,
    TaskAttachmentCreate,
    TaskCommentCreate,
    TaskCreate,
    TaskReviewCreate,
    TaskUpdate,
)
from app.shared.exceptions import AppException, NotFoundException
from app.shared.optimistic_lock import apply_version_update, check_version


# ── Constants ──

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_TASK_TYPES = {"corrective", "preventive", "inspection", "training", "capex"}
VALID_RESPONSIBILITY_TYPES = {"owner", "support", "approver"}
VALID_UPLOAD_STAGES = {"before", "during", "after", "review"}
VALID_REVIEW_RESULTS = {"approved", "rejected", "needs_rework"}
VALID_COMMENT_TYPES = {"note", "question", "update", "escalation", "rejection_reason"}

VALID_TRANSITIONS: dict[str, list[str]] = {
    "open": ["accepted", "cancelled"],
    "accepted": ["in_progress", "cancelled"],
    "in_progress": ["pending_review", "cancelled"],
    "pending_review": ["closed", "needs_rework"],
    "needs_rework": ["in_progress", "cancelled"],
    # closed / cancelled are terminal
}


# ── Validation helpers ──

def _validate_priority(p: str) -> None:
    if p not in VALID_PRIORITIES:
        raise AppException(422, "INVALID_PRIORITY", f"priority phải là: {', '.join(sorted(VALID_PRIORITIES))}")


def _validate_task_type(t: str) -> None:
    if t not in VALID_TASK_TYPES:
        raise AppException(422, "INVALID_TASK_TYPE", f"task_type phải là: {', '.join(sorted(VALID_TASK_TYPES))}")


def _validate_responsibility_type(r: str) -> None:
    if r not in VALID_RESPONSIBILITY_TYPES:
        raise AppException(422, "INVALID_RESPONSIBILITY_TYPE",
                           f"responsibility_type phải là: {', '.join(sorted(VALID_RESPONSIBILITY_TYPES))}")


def _validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise AppException(
            422,
            "INVALID_STATUS_TRANSITION",
            f"Không thể chuyển từ '{current}' sang '{target}'. Cho phép: {', '.join(allowed) or 'none'}",
        )


# ═══════════════════════════════════════════════════════════════════
# Task CRUD (B06.1)
# ═══════════════════════════════════════════════════════════════════

async def _generate_task_no(db: AsyncSession) -> str:
    """Generate unique task number: TASK-YYYY-NNNN."""
    year = datetime.now(timezone.utc).year
    prefix = f"TASK-{year}-"
    result = await db.execute(
        select(func.count())
        .select_from(CorrectiveTask)
        .where(CorrectiveTask.task_no.like(f"{prefix}%"))
    )
    count = (result.scalar() or 0) + 1
    return f"{prefix}{count:04d}"


async def create_task(
    db: AsyncSession, data: TaskCreate, created_by_user_id: uuid.UUID
) -> CorrectiveTask:
    _validate_priority(data.priority)
    _validate_task_type(data.task_type)

    # Validate case exists
    from app.cases.models import RiskCase
    result = await db.execute(select(RiskCase).where(RiskCase.id == data.case_id))
    if not result.scalar_one_or_none():
        raise NotFoundException("Risk case not found.")

    task_no = await _generate_task_no(db)

    task = CorrectiveTask(
        case_id=data.case_id,
        task_no=task_no,
        title=data.title,
        description=data.description,
        task_type=data.task_type,
        source_rca_id=data.source_rca_id,
        area_id=data.area_id,
        priority=data.priority,
        status="open",
        sla_due_at=data.sla_due_at,
        completion_due_at=data.completion_due_at,
        completion_criteria=data.completion_criteria,
        evidence_requirement=data.evidence_requirement,
        created_by_user_id=created_by_user_id,
    )
    db.add(task)
    await db.flush()

    # Add assignees
    for assignee_data in data.assignees:
        _validate_responsibility_type(assignee_data.responsibility_type)
        assignee = TaskAssignee(
            task_id=task.id,
            user_id=assignee_data.user_id,
            responsibility_type=assignee_data.responsibility_type,
        )
        db.add(assignee)

    await db.flush()
    await db.commit()
    return await get_task(db, task.id)


async def list_tasks(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    priority: str | None = None,
    status: str | None = None,
    assignee_user_id: uuid.UUID | None = None,
    overdue: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CorrectiveTask], int]:
    base = select(CorrectiveTask).where(CorrectiveTask.archived_at.is_(None))
    count_q = select(func.count()).select_from(CorrectiveTask).where(CorrectiveTask.archived_at.is_(None))

    if case_id:
        base = base.where(CorrectiveTask.case_id == case_id)
        count_q = count_q.where(CorrectiveTask.case_id == case_id)
    if farm_id:
        from app.cases.models import RiskCase
        base = base.join(RiskCase, CorrectiveTask.case_id == RiskCase.id).where(RiskCase.farm_id == farm_id)
        count_q = count_q.join(RiskCase, CorrectiveTask.case_id == RiskCase.id).where(RiskCase.farm_id == farm_id)
    if priority:
        base = base.where(CorrectiveTask.priority == priority)
        count_q = count_q.where(CorrectiveTask.priority == priority)
    if status:
        base = base.where(CorrectiveTask.status == status)
        count_q = count_q.where(CorrectiveTask.status == status)
    if assignee_user_id:
        base = base.join(TaskAssignee, CorrectiveTask.id == TaskAssignee.task_id).where(
            TaskAssignee.user_id == assignee_user_id
        )
        count_q = count_q.join(TaskAssignee, CorrectiveTask.id == TaskAssignee.task_id).where(
            TaskAssignee.user_id == assignee_user_id
        )
    if overdue:
        now = datetime.now(timezone.utc)
        non_terminal = ("open", "accepted", "in_progress", "pending_review", "needs_rework")
        base = base.where(
            CorrectiveTask.completion_due_at < now,
            CorrectiveTask.status.in_(non_terminal),
        )
        count_q = count_q.where(
            CorrectiveTask.completion_due_at < now,
            CorrectiveTask.status.in_(non_terminal),
        )

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.options(selectinload(CorrectiveTask.assignees))
        .order_by(CorrectiveTask.priority, CorrectiveTask.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().unique().all()), total


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> CorrectiveTask:
    result = await db.execute(
        select(CorrectiveTask)
        .options(
            selectinload(CorrectiveTask.assignees),
            selectinload(CorrectiveTask.reviews),
            selectinload(CorrectiveTask.comments),
            selectinload(CorrectiveTask.task_attachments),
        )
        .where(CorrectiveTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Corrective task not found.")
    return task


async def update_task(
    db: AsyncSession, task_id: uuid.UUID, data: TaskUpdate
) -> CorrectiveTask:
    task = await get_task(db, task_id)
    check_version(task.version, data.version)

    if task.status in ("closed", "cancelled"):
        raise AppException(422, "TASK_TERMINAL", "Không thể sửa task đã closed/cancelled.")

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})
    if "priority" in update_data:
        _validate_priority(update_data["priority"])

    for key, value in update_data.items():
        setattr(task, key, value)
    task.version = apply_version_update(task.version)
    await db.flush()
    await db.refresh(task)
    await db.commit()
    return await get_task(db, task.id)


# ═══════════════════════════════════════════════════════════════════
# Task State Machine (B06.2)
# ═══════════════════════════════════════════════════════════════════

async def change_status(
    db: AsyncSession, task_id: uuid.UUID, data: ChangeTaskStatusRequest, user_id: uuid.UUID
) -> CorrectiveTask:
    task = await get_task(db, task_id)
    check_version(task.version, data.version)
    _validate_transition(task.status, data.target_status)

    # BR-04: Cannot close without at least 1 approved review
    if data.target_status == "closed":
        has_approved = any(r.review_result == "approved" for r in task.reviews)
        if not has_approved:
            raise AppException(
                422,
                "NO_APPROVED_REVIEW",
                "Không thể đóng task khi chưa có review approved.",
            )
        task.closed_by_user_id = user_id
        task.closed_at = datetime.now(timezone.utc)

    task.status = data.target_status
    task.version = apply_version_update(task.version)
    await db.flush()
    await db.refresh(task)
    await db.commit()
    return await get_task(db, task.id)


# ═══════════════════════════════════════════════════════════════════
# Submit for Review (B06.4)
# ═══════════════════════════════════════════════════════════════════

async def submit_for_review(
    db: AsyncSession, task_id: uuid.UUID, version: int
) -> CorrectiveTask:
    task = await get_task(db, task_id)
    check_version(task.version, version)
    _validate_transition(task.status, "pending_review")

    # Must have at least 1 evidence attachment
    if not task.task_attachments:
        raise AppException(
            422,
            "NO_EVIDENCE",
            "Cần ít nhất 1 bằng chứng (evidence) trước khi submit for review.",
        )

    task.status = "pending_review"
    task.version = apply_version_update(task.version)
    await db.flush()
    await db.refresh(task)
    await db.commit()
    return await get_task(db, task.id)


# ═══════════════════════════════════════════════════════════════════
# Assignees (B06.3)
# ═══════════════════════════════════════════════════════════════════

async def add_assignee(
    db: AsyncSession, task_id: uuid.UUID, data: TaskAssigneeInput
) -> TaskAssignee:
    task = await get_task(db, task_id)
    _validate_responsibility_type(data.responsibility_type)

    # Check duplicate
    existing = await db.execute(
        select(TaskAssignee).where(
            TaskAssignee.task_id == task.id,
            TaskAssignee.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise AppException(409, "ASSIGNEE_EXISTS", "User đã được gán vào task này.")

    assignee = TaskAssignee(
        task_id=task.id,
        user_id=data.user_id,
        responsibility_type=data.responsibility_type,
    )
    db.add(assignee)
    await db.flush()
    await db.refresh(assignee)
    await db.commit()
    return assignee


async def remove_assignee(
    db: AsyncSession, task_id: uuid.UUID, assignee_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(TaskAssignee).where(
            TaskAssignee.id == assignee_id,
            TaskAssignee.task_id == task_id,
        )
    )
    assignee = result.scalar_one_or_none()
    if not assignee:
        raise NotFoundException("Task assignee not found.")
    await db.delete(assignee)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════
# Reviews (B06.5)
# ═══════════════════════════════════════════════════════════════════

async def list_reviews(db: AsyncSession, task_id: uuid.UUID) -> list[TaskReview]:
    await get_task(db, task_id)
    result = await db.execute(
        select(TaskReview)
        .where(TaskReview.task_id == task_id)
        .order_by(TaskReview.reviewed_at.desc())
    )
    return list(result.scalars().all())


async def create_review(
    db: AsyncSession, task_id: uuid.UUID, data: TaskReviewCreate, reviewer_user_id: uuid.UUID
) -> TaskReview:
    task = await get_task(db, task_id)

    if task.status != "pending_review":
        raise AppException(422, "NOT_PENDING_REVIEW", "Task phải ở trạng thái pending_review để review.")

    if data.review_result not in VALID_REVIEW_RESULTS:
        raise AppException(422, "INVALID_REVIEW_RESULT",
                           f"review_result phải là: {', '.join(sorted(VALID_REVIEW_RESULTS))}")

    review = TaskReview(
        task_id=task.id,
        reviewer_user_id=reviewer_user_id,
        review_result=data.review_result,
        review_note=data.review_note,
        next_action_due_at=data.next_action_due_at,
    )
    db.add(review)
    await db.flush()

    # Auto-transition based on review result
    if data.review_result == "approved":
        # Task can now be closed (don't auto-close, let user decide)
        pass
    elif data.review_result in ("rejected", "needs_rework"):
        task.status = "needs_rework"
        task.version = apply_version_update(task.version)
        await db.flush()

    await db.refresh(review)
    await db.commit()
    return review


async def approve_task(
    db: AsyncSession, task_id: uuid.UUID, reviewer_user_id: uuid.UUID, review_note: str | None = None
) -> TaskReview:
    return await create_review(
        db, task_id,
        TaskReviewCreate(review_result="approved", review_note=review_note),
        reviewer_user_id,
    )


async def reject_task(
    db: AsyncSession, task_id: uuid.UUID, reviewer_user_id: uuid.UUID,
    review_note: str | None = None, next_action_due_at: datetime | None = None
) -> TaskReview:
    return await create_review(
        db, task_id,
        TaskReviewCreate(
            review_result="needs_rework",
            review_note=review_note,
            next_action_due_at=next_action_due_at,
        ),
        reviewer_user_id,
    )


# ═══════════════════════════════════════════════════════════════════
# Comments (B06.6)
# ═══════════════════════════════════════════════════════════════════

async def create_comment(
    db: AsyncSession, task_id: uuid.UUID, data: TaskCommentCreate, author_user_id: uuid.UUID
) -> TaskComment:
    await get_task(db, task_id)

    if data.comment_type not in VALID_COMMENT_TYPES:
        raise AppException(422, "INVALID_COMMENT_TYPE",
                           f"comment_type phải là: {', '.join(sorted(VALID_COMMENT_TYPES))}")

    comment = TaskComment(
        task_id=task_id,
        author_user_id=author_user_id,
        comment_text=data.comment_text,
        comment_type=data.comment_type,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    await db.commit()
    return comment


# ═══════════════════════════════════════════════════════════════════
# Task Attachments (link attachment to task)
# ═══════════════════════════════════════════════════════════════════

async def add_task_attachment(
    db: AsyncSession, task_id: uuid.UUID, data: TaskAttachmentCreate
) -> TaskAttachment:
    await get_task(db, task_id)

    if data.upload_stage not in VALID_UPLOAD_STAGES:
        raise AppException(422, "INVALID_UPLOAD_STAGE",
                           f"upload_stage phải là: {', '.join(sorted(VALID_UPLOAD_STAGES))}")

    # Verify attachment exists
    from app.attachments.models import Attachment
    result = await db.execute(select(Attachment).where(Attachment.id == data.attachment_id))
    if not result.scalar_one_or_none():
        raise NotFoundException("Attachment not found.")

    link = TaskAttachment(
        task_id=task_id,
        attachment_id=data.attachment_id,
        upload_stage=data.upload_stage,
        is_primary_evidence=data.is_primary_evidence,
        caption=data.caption,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    await db.commit()
    return link
