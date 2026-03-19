"""Service layer for Dashboard & Analytics module (Sprint 09).

Covers:
  B09.1  Executive summary
  B09.2  Farm detail dashboard
  B09.3  Benchmark (farm comparison)
  B09.4  Trust gaps
  B09.5  Killer metrics trend
  B09.6  Scar hotspots
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.models import Assessment
from app.auth.models import Farm, Region
from app.cases.models import RiskCase
from app.killer_metrics.models import KillerMetricDefinition, KillerMetricEvent
from app.scars.models import ScarRecord
from app.shared.cache import cache_get, cache_set
from app.tasks.models import CorrectiveTask
from app.trust_scores.models import TrustScoreSnapshot

_DASHBOARD_TTL = 300  # 5 minutes


# ═══════════════════════════════════════════════════════════════════
# B09.1 — Executive Summary
# ═══════════════════════════════════════════════════════════════════

async def executive_summary(db: AsyncSession) -> dict:
    """System-wide KPIs for executive dashboard."""
    cache_key = "dashboard:executive_summary"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    now = datetime.now(timezone.utc)

    # Farm count (active)
    farm_count = (await db.execute(
        select(func.count(Farm.id)).where(Farm.operational_status == "active")
    )).scalar_one()

    # Average latest assessment overall_score across farms
    # Subquery: latest submitted assessment per farm (DISTINCT ON)
    latest_assessment = (
        select(
            Assessment.farm_id,
            Assessment.overall_score,
        )
        .where(Assessment.status != "draft")
        .distinct(Assessment.farm_id)
        .order_by(Assessment.farm_id, Assessment.assessment_date.desc())
        .subquery()
    )

    avg_score_result = (await db.execute(
        select(func.round(func.avg(latest_assessment.c.overall_score), 1))
    )).scalar_one()

    # Open cases
    open_cases = (await db.execute(
        select(func.count(RiskCase.id))
        .where(RiskCase.current_status == "open")
        .where(RiskCase.archived_at.is_(None))
    )).scalar_one()

    # Overdue tasks
    overdue_tasks = (await db.execute(
        select(func.count(CorrectiveTask.id))
        .where(CorrectiveTask.status == "open")
        .where(CorrectiveTask.archived_at.is_(None))
        .where(CorrectiveTask.sla_due_at < now)
    )).scalar_one()

    # Open killer metric events
    km_open = (await db.execute(
        select(func.count(KillerMetricEvent.id))
        .where(KillerMetricEvent.status == "open")
    )).scalar_one()

    # High-risk farms (baseline_risk_level = 'high' or 'critical')
    high_risk_farms = (await db.execute(
        select(func.count(Farm.id))
        .where(Farm.operational_status == "active")
        .where(Farm.baseline_risk_level.in_(["high", "critical"]))
    )).scalar_one()

    # Low trust sites (trust_score < 60)
    # Use latest trust snapshot per farm
    latest_trust = (
        select(
            TrustScoreSnapshot.farm_id,
            func.max(TrustScoreSnapshot.snapshot_date).label("latest_date"),
        )
        .group_by(TrustScoreSnapshot.farm_id)
        .subquery()
    )
    low_trust_sites = (await db.execute(
        select(func.count(TrustScoreSnapshot.id))
        .join(
            latest_trust,
            (TrustScoreSnapshot.farm_id == latest_trust.c.farm_id)
            & (TrustScoreSnapshot.snapshot_date == latest_trust.c.latest_date),
        )
        .where(TrustScoreSnapshot.trust_score < 60)
    )).scalar_one()

    # Trust distribution buckets
    trust_distribution = await _trust_distribution(db, latest_trust)

    result = {
        "farm_count": farm_count,
        "avg_score": float(avg_score_result) if avg_score_result else None,
        "high_risk_farms": high_risk_farms,
        "open_cases": open_cases,
        "overdue_tasks": overdue_tasks,
        "killer_metric_open": km_open,
        "low_trust_sites": low_trust_sites,
        "trust_distribution": trust_distribution,
    }
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result


async def _trust_distribution(db: AsyncSession, latest_trust_subq) -> dict:
    """Count farms by trust score bucket: high (>=80), medium (60-79), low (<60)."""
    rows = (await db.execute(
        select(
            func.count(case((TrustScoreSnapshot.trust_score >= 80, 1))).label("high"),
            func.count(case(
                (
                    (TrustScoreSnapshot.trust_score >= 60)
                    & (TrustScoreSnapshot.trust_score < 80),
                    1,
                )
            )).label("medium"),
            func.count(case((TrustScoreSnapshot.trust_score < 60, 1))).label("low"),
        )
        .join(
            latest_trust_subq,
            (TrustScoreSnapshot.farm_id == latest_trust_subq.c.farm_id)
            & (TrustScoreSnapshot.snapshot_date == latest_trust_subq.c.latest_date),
        )
    )).one()
    return {"high": rows.high, "medium": rows.medium, "low": rows.low}


# ═══════════════════════════════════════════════════════════════════
# B09.2 — Farm Detail Dashboard
# ═══════════════════════════════════════════════════════════════════

async def farm_dashboard(db: AsyncSession, farm_id) -> dict:
    """Farm-specific KPIs: scores over time, open cases/tasks, scars, trust trend."""
    import uuid
    fid = uuid.UUID(str(farm_id))

    cache_key = f"dashboard:farm:{fid}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # Assessment scores over time (last 12 months, submitted only)
    twelve_months_ago = date.today() - timedelta(days=365)
    score_rows = (await db.execute(
        select(
            cast(Assessment.assessment_date, Date).label("assessment_date"),
            Assessment.overall_score,
            Assessment.hardware_score,
            Assessment.process_score,
            Assessment.behavior_score,
            Assessment.monitoring_score,
            Assessment.assessment_type,
        )
        .where(Assessment.farm_id == fid)
        .where(Assessment.status != "draft")
        .where(cast(Assessment.assessment_date, Date) >= twelve_months_ago)
        .order_by(Assessment.assessment_date)
    )).all()

    scores_over_time = [
        {
            "date": str(r.assessment_date),
            "overall_score": float(r.overall_score) if r.overall_score else None,
            "hardware_score": float(r.hardware_score) if r.hardware_score else None,
            "process_score": float(r.process_score) if r.process_score else None,
            "behavior_score": float(r.behavior_score) if r.behavior_score else None,
            "monitoring_score": float(r.monitoring_score) if r.monitoring_score else None,
            "assessment_type": r.assessment_type,
        }
        for r in score_rows
    ]

    # Open cases count
    open_cases = (await db.execute(
        select(func.count(RiskCase.id))
        .where(RiskCase.farm_id == fid)
        .where(RiskCase.current_status == "open")
        .where(RiskCase.archived_at.is_(None))
    )).scalar_one()

    # Open tasks count (via case join)
    open_tasks = (await db.execute(
        select(func.count(CorrectiveTask.id))
        .join(RiskCase, CorrectiveTask.case_id == RiskCase.id)
        .where(RiskCase.farm_id == fid)
        .where(CorrectiveTask.status == "open")
        .where(CorrectiveTask.archived_at.is_(None))
    )).scalar_one()

    # Overdue tasks
    now = datetime.now(timezone.utc)
    overdue_tasks = (await db.execute(
        select(func.count(CorrectiveTask.id))
        .join(RiskCase, CorrectiveTask.case_id == RiskCase.id)
        .where(RiskCase.farm_id == fid)
        .where(CorrectiveTask.status == "open")
        .where(CorrectiveTask.archived_at.is_(None))
        .where(CorrectiveTask.sla_due_at < now)
    )).scalar_one()

    # Active scars count
    active_scars = (await db.execute(
        select(func.count(ScarRecord.id))
        .where(ScarRecord.farm_id == fid)
        .where(ScarRecord.status == "active")
    )).scalar_one()

    # Trust trend (all snapshots for this farm, ordered)
    trust_rows = (await db.execute(
        select(
            TrustScoreSnapshot.snapshot_date,
            TrustScoreSnapshot.trust_score,
            TrustScoreSnapshot.absolute_gap_score,
        )
        .where(TrustScoreSnapshot.farm_id == fid)
        .order_by(TrustScoreSnapshot.snapshot_date)
    )).all()

    trust_trend = [
        {
            "date": str(r.snapshot_date),
            "trust_score": float(r.trust_score) if r.trust_score else None,
            "gap_score": float(r.absolute_gap_score) if r.absolute_gap_score else None,
        }
        for r in trust_rows
    ]

    # Killer metric events count (open)
    km_open = (await db.execute(
        select(func.count(KillerMetricEvent.id))
        .where(KillerMetricEvent.farm_id == fid)
        .where(KillerMetricEvent.status == "open")
    )).scalar_one()

    result = {
        "farm_id": str(fid),
        "scores_over_time": scores_over_time,
        "open_cases": open_cases,
        "open_tasks": open_tasks,
        "overdue_tasks": overdue_tasks,
        "active_scars": active_scars,
        "killer_metric_open": km_open,
        "trust_trend": trust_trend,
    }
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result


# ═══════════════════════════════════════════════════════════════════
# B09.3 — Benchmark (Farm Comparison)
# ═══════════════════════════════════════════════════════════════════

async def benchmark(
    db: AsyncSession,
    *,
    farm_type: str | None = None,
    region_id: str | None = None,
) -> list[dict]:
    """Farm comparison: latest score, rank, percentile."""
    import uuid

    cache_key = f"dashboard:benchmark:{farm_type or 'all'}:{region_id or 'all'}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # Use PostgreSQL DISTINCT ON to get one assessment per farm (the latest).
    latest_score = (
        select(
            Assessment.farm_id,
            Assessment.overall_score,
        )
        .where(Assessment.status != "draft")
        .distinct(Assessment.farm_id)
        .order_by(Assessment.farm_id, Assessment.assessment_date.desc())
        .subquery()
    )

    query = (
        select(
            Farm.id.label("farm_id"),
            Farm.name.label("farm_name"),
            Farm.code.label("farm_code"),
            Farm.farm_type,
            Farm.ownership_type,
            Region.name.label("region_name"),
            latest_score.c.overall_score,
        )
        .join(latest_score, Farm.id == latest_score.c.farm_id, isouter=True)
        .join(Region, Farm.region_id == Region.id, isouter=True)
        .where(Farm.operational_status == "active")
    )

    if farm_type:
        query = query.where(Farm.farm_type == farm_type)
    if region_id:
        query = query.where(Farm.region_id == uuid.UUID(region_id))

    query = query.order_by(latest_score.c.overall_score.desc().nulls_last())
    rows = (await db.execute(query)).all()

    # Compute rank and percentile
    total = len(rows)
    result = []
    for rank, r in enumerate(rows, start=1):
        score = float(r.overall_score) if r.overall_score else None
        result.append({
            "farm_id": str(r.farm_id),
            "farm_name": r.farm_name,
            "farm_code": r.farm_code,
            "farm_type": r.farm_type,
            "ownership_type": r.ownership_type,
            "region_name": r.region_name,
            "overall_score": score,
            "rank": rank,
            "percentile": round((total - rank) / total * 100, 1) if total > 0 else 0,
        })
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result


# ═══════════════════════════════════════════════════════════════════
# B09.4 — Trust Gaps
# ═══════════════════════════════════════════════════════════════════

async def trust_gaps(db: AsyncSession) -> list[dict]:
    """Farms sorted by trust score, highlight low trust (<60)."""
    cache_key = "dashboard:trust_gaps"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    latest_trust = (
        select(
            TrustScoreSnapshot.farm_id,
            func.max(TrustScoreSnapshot.snapshot_date).label("latest_date"),
        )
        .group_by(TrustScoreSnapshot.farm_id)
        .subquery()
    )

    rows = (await db.execute(
        select(
            Farm.id.label("farm_id"),
            Farm.name.label("farm_name"),
            Farm.code.label("farm_code"),
            Farm.farm_type,
            Region.name.label("region_name"),
            TrustScoreSnapshot.trust_score,
            TrustScoreSnapshot.absolute_gap_score,
            TrustScoreSnapshot.snapshot_date,
        )
        .join(
            latest_trust,
            Farm.id == latest_trust.c.farm_id,
        )
        .join(
            TrustScoreSnapshot,
            (TrustScoreSnapshot.farm_id == latest_trust.c.farm_id)
            & (TrustScoreSnapshot.snapshot_date == latest_trust.c.latest_date),
        )
        .join(Region, Farm.region_id == Region.id, isouter=True)
        .where(Farm.operational_status == "active")
        .order_by(TrustScoreSnapshot.trust_score.asc())
    )).all()

    result = [
        {
            "farm_id": str(r.farm_id),
            "farm_name": r.farm_name,
            "farm_code": r.farm_code,
            "farm_type": r.farm_type,
            "region_name": r.region_name,
            "trust_score": float(r.trust_score) if r.trust_score else None,
            "gap_score": float(r.absolute_gap_score) if r.absolute_gap_score else None,
            "snapshot_date": str(r.snapshot_date),
            "is_low_trust": r.trust_score is not None and float(r.trust_score) < 60,
        }
        for r in rows
    ]
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result


# ═══════════════════════════════════════════════════════════════════
# B09.5 — Killer Metrics Trend
# ═══════════════════════════════════════════════════════════════════

async def killer_metrics_trend(
    db: AsyncSession,
    *,
    farm_id: str | None = None,
    months: int = 6,
) -> list[dict]:
    """Timeline of killer metric events by month, type, status."""
    import uuid

    cache_key = f"dashboard:km_trend:{farm_id or 'all'}:{months}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    cutoff = date.today() - timedelta(days=months * 30)

    month_col = func.date_trunc("month", KillerMetricEvent.event_at).label("month")

    query = (
        select(
            month_col,
            KillerMetricDefinition.name.label("metric_name"),
            KillerMetricDefinition.code.label("metric_code"),
            KillerMetricEvent.status,
            func.count(KillerMetricEvent.id).label("event_count"),
        )
        .join(
            KillerMetricDefinition,
            KillerMetricEvent.definition_id == KillerMetricDefinition.id,
        )
        .where(cast(KillerMetricEvent.event_at, Date) >= cutoff)
    )

    if farm_id:
        query = query.where(KillerMetricEvent.farm_id == uuid.UUID(farm_id))

    query = query.group_by(
        month_col,
        KillerMetricDefinition.name,
        KillerMetricDefinition.code,
        KillerMetricEvent.status,
    ).order_by(month_col)

    rows = (await db.execute(query)).all()

    result = [
        {
            "month": r.month.strftime("%Y-%m") if r.month else None,
            "metric_name": r.metric_name,
            "metric_code": r.metric_code,
            "status": r.status,
            "event_count": r.event_count,
        }
        for r in rows
    ]
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result


# ═══════════════════════════════════════════════════════════════════
# B09.6 — Scar Hotspots
# ═══════════════════════════════════════════════════════════════════

async def scar_hotspots(
    db: AsyncSession,
    *,
    farm_id: str | None = None,
) -> list[dict]:
    """Aggregated scar count by farm, scar_type, recurrence."""
    import uuid

    cache_key = f"dashboard:scar_hotspots:{farm_id or 'all'}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    query = (
        select(
            Farm.id.label("farm_id"),
            Farm.name.label("farm_name"),
            Farm.code.label("farm_code"),
            ScarRecord.scar_type,
            func.count(ScarRecord.id).label("scar_count"),
            func.sum(case((ScarRecord.recurrence_flag.is_(True), 1), else_=0)).label(
                "recurring_count"
            ),
            func.sum(ScarRecord.recurrence_count).label("total_recurrence"),
        )
        .join(Farm, ScarRecord.farm_id == Farm.id)
        .where(ScarRecord.status == "active")
    )

    if farm_id:
        query = query.where(ScarRecord.farm_id == uuid.UUID(farm_id))

    query = query.group_by(
        Farm.id, Farm.name, Farm.code, ScarRecord.scar_type
    ).order_by(func.count(ScarRecord.id).desc())

    rows = (await db.execute(query)).all()

    result = [
        {
            "farm_id": str(r.farm_id),
            "farm_name": r.farm_name,
            "farm_code": r.farm_code,
            "scar_type": r.scar_type,
            "scar_count": r.scar_count,
            "recurring_count": r.recurring_count,
            "total_recurrence": r.total_recurrence or 0,
        }
        for r in rows
    ]
    await cache_set(cache_key, result, _DASHBOARD_TTL)
    return result
