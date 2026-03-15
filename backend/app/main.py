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

app.include_router(auth_router, prefix=settings.API_V1_PREFIX + "/auth", tags=["auth"])
