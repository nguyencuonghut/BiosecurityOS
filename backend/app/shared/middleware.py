"""Request ID middleware and audit logger middleware."""

import uuid
from datetime import datetime, timezone

from fastapi import Request


async def request_id_middleware(request: Request, call_next):
    """Assign a unique request_id to every request."""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


async def audit_log_middleware(request: Request, call_next):
    """Log mutating requests to audit_log table.

    NOTE: Full audit logging (writing to DB with before/after JSON)
    will be implemented at the service layer per entity, not as generic middleware.
    This middleware captures request metadata for correlation.
    """
    request.state.audit_timestamp = datetime.now(timezone.utc)
    response = await call_next(request)
    return response
