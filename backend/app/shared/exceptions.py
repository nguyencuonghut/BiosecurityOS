"""Standardized exception & error response handling.

Response format follows API contract spec (api_contracts_v2 §2.3, §2.4):
  Success: { data: {}, meta: { request_id, timestamp } }
  Error:   { error: { code, message, details }, meta: { request_id, timestamp } }
"""

from datetime import UTC, datetime

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ── Helpers ─────────────────────────────────────────────────────

def _build_meta(request: Request) -> dict:
    """Build standard meta block with request_id + timestamp."""
    return {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def success_response(request: Request, data, *, status_code: int = 200, headers: dict | None = None) -> JSONResponse:
    """Wrap any data in the standard success envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"data": data, "meta": _build_meta(request)},
        headers=headers,
    )


# ── Exceptions ──────────────────────────────────────────────────

class AppException(HTTPException):
    """Base application exception with structured error code."""

    def __init__(self, status_code: int, code: str, message: str, details: list | None = None):
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(status_code=status_code, detail=message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, code="NOT_FOUND", message=message)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource version conflict"):
        super().__init__(status_code=409, code="OPTIMISTIC_LOCK_CONFLICT", message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status_code=403, code="FORBIDDEN", message=message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message)


class ValidationException(AppException):
    def __init__(self, message: str, details: list | None = None):
        super().__init__(status_code=422, code="VALIDATION_ERROR", message=message, details=details)


class AttachmentPolicyViolation(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=400, code="ATTACHMENT_POLICY_VIOLATION", message=message)


# ── Exception handlers (register on FastAPI app) ────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "meta": _build_meta(request),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Re-format Pydantic / FastAPI 422 errors into standard error envelope."""
    details = []
    for err in exc.errors():
        details.append({
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
            },
            "meta": _build_meta(request),
        },
    )
