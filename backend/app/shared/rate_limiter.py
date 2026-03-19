"""Redis-based rate limiting middleware (Sprint 11).

Global: 100 requests/min/user
Upload: 30 files/min/user
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.cache import get_redis

_GLOBAL_LIMIT = 100
_GLOBAL_WINDOW = 60
_UPLOAD_LIMIT = 30
_UPLOAD_WINDOW = 60


def _get_client_id(request: Request) -> str:
    """Extract user id from JWT state or fall back to IP."""
    user = getattr(request.state, "current_user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return f"ip:{ip}"


async def rate_limit_middleware(request: Request, call_next):
    """Check global + upload rate limits before processing."""
    client_id = _get_client_id(request)

    try:
        r = await get_redis()

        # Global rate limit
        global_key = f"rl:global:{client_id}"
        current = await r.incr(global_key)
        if current == 1:
            await r.expire(global_key, _GLOBAL_WINDOW)
        if current > _GLOBAL_LIMIT:
            ttl = await r.ttl(global_key)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {ttl}s.",
                    }
                },
                headers={"Retry-After": str(ttl)},
            )

        # Upload rate limit (POST with multipart)
        is_upload = (
            request.method == "POST"
            and "multipart/form-data" in (request.headers.get("content-type") or "")
        )
        if is_upload:
            upload_key = f"rl:upload:{client_id}"
            ucurrent = await r.incr(upload_key)
            if ucurrent == 1:
                await r.expire(upload_key, _UPLOAD_WINDOW)
            if ucurrent > _UPLOAD_LIMIT:
                ttl = await r.ttl(upload_key)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "UPLOAD_RATE_LIMIT_EXCEEDED",
                            "message": f"Upload rate limit exceeded. Try again in {ttl}s.",
                        }
                    },
                    headers={"Retry-After": str(ttl)},
                )
    except Exception:
        # If Redis is down, allow request through (fail-open)
        pass

    return await call_next(request)
