"""Notification service (B10.4 CRUD + B10.5 trigger rules)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.killer_metrics.notification_model import Notification
from app.notifications.schemas import NotificationCreate


# ═══════════════════════════════════════════════════════════════
# B10.4 — CRUD
# ═══════════════════════════════════════════════════════════════

async def list_notifications(
    db: AsyncSession,
    *,
    recipient_user_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    """List notifications for a user, newest first."""
    base = select(Notification).where(Notification.recipient_user_id == recipient_user_id)
    if status:
        base = base.where(Notification.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    rows = (
        await db.execute(
            base.order_by(Notification.sent_at.desc().nulls_last())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return list(rows), total


async def get_unread_count(db: AsyncSession, *, recipient_user_id: uuid.UUID) -> int:
    """Count unread notifications for badge display."""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.recipient_user_id == recipient_user_id)
        .where(Notification.read_at.is_(None))
        .where(Notification.status.in_(["queued", "sent"]))
    )
    return result.scalar_one()


async def mark_read(db: AsyncSession, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.recipient_user_id == user_id)
        .where(Notification.read_at.is_(None))
        .values(read_at=now, status="read")
    )
    await db.commit()
    return result.rowcount > 0


async def bulk_mark_read(
    db: AsyncSession,
    *,
    notification_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> int:
    """Mark multiple notifications as read. Returns count updated."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(Notification)
        .where(Notification.id.in_(notification_ids))
        .where(Notification.recipient_user_id == user_id)
        .where(Notification.read_at.is_(None))
        .values(read_at=now, status="read")
    )
    await db.commit()
    return result.rowcount


# ═══════════════════════════════════════════════════════════════
# B10.5 — Trigger rules (create notification from service events)
# ═══════════════════════════════════════════════════════════════

async def create_notification(db: AsyncSession, *, data: NotificationCreate) -> Notification:
    """Create a single in-app notification."""
    now = datetime.now(UTC)
    notif = Notification(
        recipient_user_id=data.recipient_user_id,
        channel=data.channel,
        title=data.title,
        body=data.body,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        status="sent",
        sent_at=now,
    )
    db.add(notif)
    await db.flush()
    return notif


async def notify_users(
    db: AsyncSession,
    *,
    recipient_user_ids: list[uuid.UUID],
    title: str,
    body: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    channel: str = "in_app",
) -> list[Notification]:
    """Broadcast a notification to multiple users."""
    notifications = []
    now = datetime.now(UTC)
    for uid in recipient_user_ids:
        notif = Notification(
            recipient_user_id=uid,
            channel=channel,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            status="sent",
            sent_at=now,
        )
        db.add(notif)
        notifications.append(notif)
    await db.flush()
    return notifications
