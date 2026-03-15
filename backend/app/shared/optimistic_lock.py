"""Optimistic locking utility — ETag / If-Match / version check.

API contract §2.11:
  - GET responses include `version` in payload + `ETag` header.
  - PATCH/POST state changes require `If-Match: <version>` header.
  - Server returns 409 if version mismatch.

Usage:
    # In a PATCH endpoint:
    @router.patch("/items/{id}")
    async def update_item(
        ...,
        if_match_version: Annotated[int, Depends(require_if_match)],
    ):
        check_version(item.version, if_match_version)
        item.version = apply_version_update(item.version)
        ...
        return success_response(request, data, headers=etag_headers(item.version))
"""

from typing import Annotated

from fastapi import Header

from app.shared.exceptions import ConflictException, ValidationException


def check_version(current_version: int, expected_version: int) -> None:
    """Raise 409 Conflict if versions don't match."""
    if current_version != expected_version:
        raise ConflictException(
            message=f"Resource was modified by another request. Expected version {expected_version}, "
            f"current version is {current_version}. Please refresh and try again."
        )


def apply_version_update(current_version: int) -> int:
    """Return the next version number after a successful optimistic-lock check."""
    return current_version + 1


def etag_headers(version: int) -> dict[str, str]:
    """Build ETag response header dict from version."""
    return {"ETag": f'"{version}"'}


def parse_if_match(if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> int | None:
    """Parse If-Match header value to integer version. Returns None if header is absent."""
    if if_match is None:
        return None
    cleaned = if_match.strip().strip('"')
    try:
        return int(cleaned)
    except ValueError:
        return None


def require_if_match(if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> int:
    """Like parse_if_match but raises 422 if header is missing or invalid.

    Use as Depends(require_if_match) on PATCH/state-change endpoints.
    """
    if if_match is None:
        raise ValidationException("If-Match header is required for this operation.")
    cleaned = if_match.strip().strip('"')
    try:
        return int(cleaned)
    except ValueError:
        raise ValidationException(f"Invalid If-Match header value: '{if_match}'. Must be an integer version.")
