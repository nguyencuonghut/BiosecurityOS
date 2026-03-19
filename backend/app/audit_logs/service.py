"""Audit log admin service (B10.7)."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuditLog


async def list_audit_logs(
    db: AsyncSession,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """Query audit logs with filters, paginated, newest first."""
    base = select(AuditLog)

    if entity_type:
        base = base.where(AuditLog.entity_type == entity_type)
    if entity_id:
        base = base.where(AuditLog.entity_id == entity_id)
    if actor_user_id:
        base = base.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        base = base.where(AuditLog.action.ilike(f"%{action}%"))
    if date_from:
        base = base.where(func.date(AuditLog.occurred_at) >= date_from)
    if date_to:
        base = base.where(func.date(AuditLog.occurred_at) <= date_to)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    rows = (
        await db.execute(
            base.order_by(AuditLog.occurred_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items = []
    for r in rows:
        items.append({
            "id": str(r.id),
            "actor_user_id": str(r.actor_user_id),
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "before_json": r.before_json,
            "after_json": r.after_json,
            "ip_address": str(r.ip_address) if r.ip_address else None,
            "user_agent": r.user_agent,
            "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
        })

    return items, total
