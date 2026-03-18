"""API router for Dashboard & Analytics module (Sprint 09).

6 read-only endpoints — all require DASHBOARD_VIEW permission.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_permission
from app.dashboards import service
from app.database import get_db
from app.shared.exceptions import success_response

dashboard_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# B09.1 — Executive Summary
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/executive-summary",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def executive_summary(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await service.executive_summary(db)
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# B09.2 — Farm Detail Dashboard
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/farm/{farm_id}",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def farm_dashboard(
    farm_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await service.farm_dashboard(db, farm_id)
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# B09.3 — Benchmark
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/benchmark",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def benchmark(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_type: Annotated[str | None, Query()] = None,
    region_id: Annotated[str | None, Query()] = None,
):
    data = await service.benchmark(db, farm_type=farm_type, region_id=region_id)
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# B09.4 — Trust Gaps
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/trust-gaps",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def trust_gaps(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await service.trust_gaps(db)
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# B09.5 — Killer Metrics Trend
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/killer-metrics-trend",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def killer_metrics_trend(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_id: Annotated[str | None, Query()] = None,
    months: Annotated[int, Query(ge=1, le=24)] = 6,
):
    data = await service.killer_metrics_trend(db, farm_id=farm_id, months=months)
    return success_response(request, data)


# ═══════════════════════════════════════════════════════════════════
# B09.6 — Scar Hotspots
# ═══════════════════════════════════════════════════════════════════

@dashboard_router.get(
    "/scar-hotspots",
    dependencies=[require_permission("DASHBOARD_VIEW")],
)
async def scar_hotspots(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    farm_id: Annotated[str | None, Query()] = None,
):
    data = await service.scar_hotspots(db, farm_id=farm_id)
    return success_response(request, data)
