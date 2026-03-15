"""Pagination utilities for list endpoints.

Usage in a router:
    @router.get("/items")
    async def list_items(
        request: Request,
        pagination: Annotated[PaginationParams, Depends()],
        db: Annotated[AsyncSession, Depends(get_db)],
    ):
        query = select(Item)
        query = pagination.apply_sort(query, Item)        # optional
        items = ...                                       # paginate
        return paginated_response(request, items, total, pagination)
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select


class PaginationParams:
    """Injectable pagination + sort parameters (use with Depends())."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
        sort: Annotated[str | None, Query(description="Sort field, prefix - for desc")] = None,
    ):
        self.page = page
        self.page_size = page_size
        self.sort = sort

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def apply_sort(self, query: Select, model: type[DeclarativeBase]) -> Select:
        """Apply sort parameter to a SQLAlchemy select.

        Example sort values: "created_at", "-created_at", "name"
        """
        if not self.sort:
            return query
        descending = self.sort.startswith("-")
        field_name = self.sort.lstrip("-")
        column = getattr(model, field_name, None)
        if column is None:
            return query
        return query.order_by(desc(column) if descending else asc(column))


def paginated_response(
    request: Request,
    items: list[Any],
    total: int,
    pagination: PaginationParams,
) -> dict:
    """Build a paginated response dict matching API contract §2.5."""
    return {
        "data": items,
        "meta": {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "total_pages": (total + pagination.page_size - 1) // pagination.page_size
            if pagination.page_size > 0
            else 0,
            "request_id": getattr(request.state, "request_id", None),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
