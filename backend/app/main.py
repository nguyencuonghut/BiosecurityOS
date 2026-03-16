"""BIOSECURITY OS 2026 — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.shared.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.shared.middleware import audit_log_middleware, request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle — replaces deprecated @app.on_event."""
    # ── Startup ──
    # Connection pools are lazily initialized by SQLAlchemy and Redis clients
    yield
    # ── Shutdown ──
    from app.database import engine

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
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(audit_log_middleware)
app.middleware("http")(request_id_middleware)

# ── Exception handlers ──
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# ── Health check ──
@app.get("/health", tags=["infra"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


# ── API routers (will be added as modules are implemented) ──
from app.auth.router import router as auth_router
from app.regions.router import router as regions_router
from app.users.router import router as users_router
from app.farms.router import router as farms_router
from app.scorecards.router import router as scorecards_router
from app.scorecards.router import section_router as scorecard_sections_router
from app.scorecards.router import item_router as scorecard_items_router
from app.assessments.router import router as assessments_router

# Ensure all ORM models are discovered by SQLAlchemy
import app.farms.models as _farms_models  # noqa: F401
import app.scorecards.models as _scorecards_models  # noqa: F401
import app.assessments.models as _assessments_models  # noqa: F401

app.include_router(auth_router, prefix=settings.API_V1_PREFIX + "/auth", tags=["auth"])
app.include_router(regions_router, prefix=settings.API_V1_PREFIX + "/regions", tags=["regions"])
app.include_router(users_router, prefix=settings.API_V1_PREFIX + "/users", tags=["users"])
app.include_router(farms_router, prefix=settings.API_V1_PREFIX + "/farms", tags=["farms"])
app.include_router(scorecards_router, prefix=settings.API_V1_PREFIX + "/scorecard-templates", tags=["scorecards"])
app.include_router(scorecard_sections_router, prefix=settings.API_V1_PREFIX + "/scorecard-sections", tags=["scorecards"])
app.include_router(scorecard_items_router, prefix=settings.API_V1_PREFIX + "/scorecard-items", tags=["scorecards"])
app.include_router(assessments_router, prefix=settings.API_V1_PREFIX + "/assessments", tags=["assessments"])
