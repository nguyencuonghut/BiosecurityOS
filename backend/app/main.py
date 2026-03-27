"""BIOSECURITY OS 2026 — FastAPI Application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.shared.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.shared.middleware import audit_log_middleware, request_id_middleware, security_headers_middleware
from app.shared.rate_limiter import rate_limit_middleware

logger = logging.getLogger(__name__)

# ── Prometheus metrics (B11.8) ──────────────────────────────────
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
        REGISTRY,
    )
    import time as _time

    _http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    _http_request_duration = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed — /metrics endpoint disabled.")


async def _prometheus_middleware(request, call_next):
    """Record request count and duration for Prometheus scraping."""
    if not _PROMETHEUS_AVAILABLE:
        return await call_next(request)
    start = _time.perf_counter()
    response = await call_next(request)
    duration = _time.perf_counter() - start
    # Use route path template (e.g. /api/v1/farms/{farm_id}) to avoid high cardinality
    route = request.scope.get("route")
    endpoint = route.path if route else request.url.path
    _http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    _http_request_duration.labels(method=request.method, endpoint=endpoint).observe(duration)
    return response


# ── Token cleanup background task (B11.7) ──────────────────────
async def _token_cleanup_loop() -> None:
    """Periodically delete expired / revoked refresh tokens (every 1 hour)."""
    from app.database import async_session_factory
    from app.auth.service import cleanup_expired_refresh_tokens

    while True:
        await asyncio.sleep(3600)  # wait 1 hour before first run
        try:
            async with async_session_factory() as db:
                deleted = await cleanup_expired_refresh_tokens(db)
            logger.info("Token cleanup: deleted %d expired/revoked refresh tokens.", deleted)
        except Exception as exc:  # noqa: BLE001
            logger.error("Token cleanup failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle — replaces deprecated @app.on_event."""
    # ── Startup ──
    cleanup_task = asyncio.create_task(_token_cleanup_loop())
    yield
    # ── Shutdown ──
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    from app.database import engine
    from app.shared.cache import close_redis

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ── Middleware (order matters: last added = first executed) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(audit_log_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_id_middleware)
if _PROMETHEUS_AVAILABLE:
    app.middleware("http")(_prometheus_middleware)

# ── Exception handlers ──
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# ── Health check ──
@app.get("/health", tags=["infra"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


# ── Prometheus metrics (B11.8) ──────────────────────────────────
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus scrape endpoint. Restricted to internal/ops access in production."""
    if not _PROMETHEUS_AVAILABLE:
        return Response(content="prometheus_client not installed", status_code=503)
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


# ── API routers (will be added as modules are implemented) ──
from app.auth.router import router as auth_router
from app.regions.router import router as regions_router
from app.users.router import router as users_router
from app.farms.router import router as farms_router
from app.scorecards.router import router as scorecards_router
from app.scorecards.router import section_router as scorecard_sections_router
from app.scorecards.router import item_router as scorecard_items_router
from app.assessments.router import router as assessments_router
from app.killer_metrics.router import definition_router as killer_def_router
from app.killer_metrics.router import event_router as killer_event_router
from app.trust_scores.router import router as trust_scores_router
from app.cases.router import case_router, rca_router, rca_factor_router
from app.tasks.router import task_router
from app.attachments.router import attachment_router
from app.floorplans.router import farm_floorplan_router, floorplan_router
from app.scars.router import scar_router, scar_map_router
from app.lessons.router import lesson_router, lesson_search_router
from app.dashboards.router import dashboard_router
from app.notifications.router import router as notification_router
from app.audit_logs.router import router as audit_log_router
from app.reports.router import router as report_router

# Ensure all ORM models are discovered by SQLAlchemy
import app.farms.models as _farms_models  # noqa: F401
import app.scorecards.models as _scorecards_models  # noqa: F401
import app.assessments.models as _assessments_models  # noqa: F401
import app.killer_metrics.models as _killer_metrics_models  # noqa: F401
import app.killer_metrics.notification_model as _notification_model  # noqa: F401
import app.trust_scores.models as _trust_scores_models  # noqa: F401
import app.cases.models as _cases_models  # noqa: F401
import app.tasks.models as _tasks_models  # noqa: F401
import app.attachments.models as _attachments_models  # noqa: F401
import app.floorplans.models as _floorplans_models  # noqa: F401
import app.scars.models as _scars_models  # noqa: F401
import app.lessons.models as _lessons_models  # noqa: F401
import app.reports.models as _reports_models  # noqa: F401

app.include_router(auth_router, prefix=settings.API_V1_PREFIX + "/auth", tags=["auth"])
app.include_router(regions_router, prefix=settings.API_V1_PREFIX + "/regions", tags=["regions"])
app.include_router(users_router, prefix=settings.API_V1_PREFIX + "/users", tags=["users"])
app.include_router(farms_router, prefix=settings.API_V1_PREFIX + "/farms", tags=["farms"])
app.include_router(scorecards_router, prefix=settings.API_V1_PREFIX + "/scorecard-templates", tags=["scorecards"])
app.include_router(scorecard_sections_router, prefix=settings.API_V1_PREFIX + "/scorecard-sections", tags=["scorecards"])
app.include_router(scorecard_items_router, prefix=settings.API_V1_PREFIX + "/scorecard-items", tags=["scorecards"])
app.include_router(assessments_router, prefix=settings.API_V1_PREFIX + "/assessments", tags=["assessments"])
app.include_router(killer_def_router, prefix=settings.API_V1_PREFIX + "/killer-metric-definitions", tags=["killer-metrics"])
app.include_router(killer_event_router, prefix=settings.API_V1_PREFIX + "/killer-metric-events", tags=["killer-metrics"])
app.include_router(trust_scores_router, prefix=settings.API_V1_PREFIX + "/trust-scores", tags=["trust-scores"])
app.include_router(case_router, prefix=settings.API_V1_PREFIX + "/cases", tags=["cases"])
app.include_router(rca_router, prefix=settings.API_V1_PREFIX + "/rca-records", tags=["rca"])
app.include_router(rca_factor_router, prefix=settings.API_V1_PREFIX + "/rca-factors", tags=["rca"])
app.include_router(task_router, prefix=settings.API_V1_PREFIX + "/tasks", tags=["tasks"])
app.include_router(attachment_router, prefix=settings.API_V1_PREFIX + "/attachments", tags=["attachments"])
app.include_router(farm_floorplan_router, prefix=settings.API_V1_PREFIX + "/farms", tags=["floorplans"])
app.include_router(floorplan_router, prefix=settings.API_V1_PREFIX + "/floorplans", tags=["floorplans"])
app.include_router(scar_router, prefix=settings.API_V1_PREFIX + "/scars", tags=["scars"])
app.include_router(scar_map_router, prefix=settings.API_V1_PREFIX + "/farms", tags=["scars"])
app.include_router(lesson_router, prefix=settings.API_V1_PREFIX + "/lessons", tags=["lessons"])
app.include_router(lesson_search_router, prefix=settings.API_V1_PREFIX + "/lessons/search", tags=["lessons"])
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX + "/dashboards", tags=["dashboards"])
app.include_router(notification_router, prefix=settings.API_V1_PREFIX + "/notifications", tags=["notifications"])
app.include_router(audit_log_router, prefix=settings.API_V1_PREFIX + "/audit-logs", tags=["audit-logs"])
app.include_router(report_router, prefix=settings.API_V1_PREFIX + "/reports", tags=["reports"])
