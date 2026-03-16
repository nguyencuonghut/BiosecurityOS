"""Service layer for Trust Score module (Sprint 04).

Covers: B04.1 Calculate, B04.2 Formula, B04.3 Snapshot storage, B04.4 Latest.

Trust Score formula (FR-09a Phase 1):
    gap        = self_overall_score - audit_overall_score
    abs_gap    = |gap|
    penalty    = 1.5 if gap > 0 (khai khống), else 1.0
    trust_score = max(0, 100 - abs_gap × penalty × severity_factor)
    severity_factor = 1.0 (Phase 1)
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.models import Assessment
from app.shared.exceptions import AppException, NotFoundException
from app.trust_scores.models import TrustScoreSnapshot
from app.trust_scores.schemas import TrustScoreCalculateRequest


# ═══════════════════════════════════════════════════════════════════
# B04.1 + B04.2 — Calculate Trust Score
# ═══════════════════════════════════════════════════════════════════

async def calculate_trust_score(
    db: AsyncSession, data: TrustScoreCalculateRequest
) -> dict:
    """Calculate and persist Trust Score from a self + audit assessment pair."""
    if data.self_assessment_id == data.audit_assessment_id:
        raise AppException(400, "SAME_ASSESSMENT", "Self assessment và audit assessment phải khác nhau.")

    self_ass = await _get_assessment(db, data.self_assessment_id, "self")
    audit_ass = await _get_assessment(db, data.audit_assessment_id, "audit")

    # Both must belong to the same farm
    if self_ass.farm_id != data.farm_id or audit_ass.farm_id != data.farm_id:
        raise AppException(400, "FARM_MISMATCH", "Cả hai assessment phải thuộc cùng trại.")

    # Both must be submitted/reviewed/locked (not draft)
    for label, ass in [("Self", self_ass), ("Audit", audit_ass)]:
        if ass.status == "draft":
            raise AppException(400, "DRAFT_ASSESSMENT", f"{label} assessment vẫn ở trạng thái draft.")
        if ass.overall_score is None:
            raise AppException(400, "NO_SCORE", f"{label} assessment chưa có overall_score.")

    self_score = float(self_ass.overall_score)
    audit_score = float(audit_ass.overall_score)

    # ── Formula (FR-09a Phase 1) ──
    gap = self_score - audit_score
    abs_gap = abs(gap)
    penalty = 1.5 if gap > 0 else 1.0
    severity_factor = 1.0  # Phase 1 default
    trust_score = max(0.0, 100.0 - abs_gap * penalty * severity_factor)

    # ── B04.3: Persist snapshot ──
    # Check if snapshot already exists for this pair (upsert)
    existing = await db.execute(
        select(TrustScoreSnapshot).where(
            TrustScoreSnapshot.farm_id == data.farm_id,
            TrustScoreSnapshot.source_self_assessment_id == data.self_assessment_id,
            TrustScoreSnapshot.source_audit_assessment_id == data.audit_assessment_id,
        )
    )
    snapshot = existing.scalar_one_or_none()

    if snapshot:
        snapshot.trust_score = Decimal(str(round(trust_score, 2)))
        snapshot.absolute_gap_score = Decimal(str(round(abs_gap, 2)))
        snapshot.severity_factor = Decimal(str(severity_factor))
        snapshot.note = _build_note(gap, penalty)
    else:
        snapshot = TrustScoreSnapshot(
            farm_id=data.farm_id,
            source_self_assessment_id=data.self_assessment_id,
            source_audit_assessment_id=data.audit_assessment_id,
            trust_score=Decimal(str(round(trust_score, 2))),
            absolute_gap_score=Decimal(str(round(abs_gap, 2))),
            severity_factor=Decimal(str(severity_factor)),
            note=_build_note(gap, penalty),
        )
        db.add(snapshot)

    await db.flush()
    await db.refresh(snapshot)
    await db.commit()

    return {
        "id": str(snapshot.id),
        "farm_id": str(snapshot.farm_id),
        "source_self_assessment_id": str(data.self_assessment_id),
        "source_audit_assessment_id": str(data.audit_assessment_id),
        "self_overall_score": self_score,
        "audit_overall_score": audit_score,
        "gap": round(gap, 2),
        "abs_gap": round(abs_gap, 2),
        "penalty": penalty,
        "severity_factor": severity_factor,
        "trust_score": round(trust_score, 2),
        "absolute_gap_score": round(abs_gap, 2),
        "snapshot_date": str(snapshot.snapshot_date),
        "formula_breakdown": {
            "step1_gap": round(gap, 2),
            "step2_abs_gap": round(abs_gap, 2),
            "step3_penalty": penalty,
            "step4_severity_factor": severity_factor,
            "step5_trust_score": round(trust_score, 2),
        },
        "note": snapshot.note,
    }


# ═══════════════════════════════════════════════════════════════════
# B04.3 — List snapshots
# ═══════════════════════════════════════════════════════════════════

async def list_snapshots(
    db: AsyncSession,
    *,
    farm_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[TrustScoreSnapshot], int]:
    from sqlalchemy import func as sqlfunc

    base = select(TrustScoreSnapshot)
    count_q = select(sqlfunc.count()).select_from(TrustScoreSnapshot)

    if farm_id:
        base = base.where(TrustScoreSnapshot.farm_id == farm_id)
        count_q = count_q.where(TrustScoreSnapshot.farm_id == farm_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(TrustScoreSnapshot.snapshot_date.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


# ═══════════════════════════════════════════════════════════════════
# B04.4 — Get latest trust score for a farm
# ═══════════════════════════════════════════════════════════════════

async def get_latest_trust_score(db: AsyncSession, farm_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(TrustScoreSnapshot)
        .where(TrustScoreSnapshot.farm_id == farm_id)
        .order_by(TrustScoreSnapshot.snapshot_date.desc())
        .limit(2)
    )
    rows = list(result.scalars().all())

    if not rows:
        raise NotFoundException("Chưa có trust score cho trại này.")

    latest = rows[0]
    response = {
        "id": str(latest.id),
        "farm_id": str(latest.farm_id),
        "trust_score": float(latest.trust_score),
        "absolute_gap_score": float(latest.absolute_gap_score),
        "severity_factor": float(latest.severity_factor) if latest.severity_factor else None,
        "snapshot_date": str(latest.snapshot_date),
        "note": latest.note,
    }

    # Comparison to previous
    if len(rows) >= 2:
        prev = rows[1]
        change = float(latest.trust_score) - float(prev.trust_score)
        response["previous_trust_score"] = float(prev.trust_score)
        response["previous_date"] = str(prev.snapshot_date)
        response["change"] = round(change, 2)
        response["trend"] = "up" if change > 0 else "down" if change < 0 else "stable"
    else:
        response["previous_trust_score"] = None
        response["previous_date"] = None
        response["change"] = None
        response["trend"] = None

    return response


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

async def _get_assessment(db: AsyncSession, assessment_id: uuid.UUID, label: str) -> Assessment:
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    ass = result.scalar_one_or_none()
    if not ass:
        raise NotFoundException(f"{label.capitalize()} assessment không tìm thấy.")
    return ass


def _build_note(gap: float, penalty: float) -> str:
    if gap > 0:
        return f"Tự đánh giá cao hơn audit {abs(gap):.1f} điểm; khai khống nên penalty {penalty}x"
    elif gap < 0:
        return f"Tự đánh giá thấp hơn audit {abs(gap):.1f} điểm; khai thấp hơn nên penalty {penalty}x"
    else:
        return "Tự đánh giá khớp với audit; Trust Score = 100"
