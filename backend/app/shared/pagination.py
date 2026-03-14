"""Pagination utilities for list endpoints."""

from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel


class PaginationParams:
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


class PaginatedResponse(BaseModel):
    data: list[Any]
    meta: dict

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int) -> "PaginatedResponse":
        return cls(
            data=items,
            meta={
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        )
