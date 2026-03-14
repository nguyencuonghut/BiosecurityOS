"""Optimistic locking utility — ETag / If-Match / version check."""

from typing import Annotated

from fastapi import Header

from app.shared.exceptions import ConflictException


def check_version(current_version: int, expected_version: int) -> None:
    """Raise 409 Conflict if versions don't match."""
    if current_version != expected_version:
        raise ConflictException(
            message=f"Resource was modified by another request. Expected version {expected_version}, "
            f"current version is {current_version}. Please refresh and try again."
        )


def parse_if_match(if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> int | None:
    """Parse If-Match header value to integer version."""
    if if_match is None:
        return None
    cleaned = if_match.strip().strip('"')
    try:
        return int(cleaned)
    except ValueError:
        return None
