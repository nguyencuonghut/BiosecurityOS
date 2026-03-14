"""Standardized exception & error response handling."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppException(HTTPException):
    """Base application exception with structured error code."""

    def __init__(self, status_code: int, code: str, message: str, details: list | None = None):
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(status_code=status_code, detail=message)


class NotFoundException(AppException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=f"{entity} with id '{entity_id}' not found",
        )


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


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "meta": {
                "request_id": _request.state.request_id if hasattr(_request.state, "request_id") else None,
            },
        },
    )
