"""Tests for B01.8 — Exception handlers & pagination."""

import pytest


# ── Error response format (§2.4) ──────────────────────────────


async def test_app_exception_has_standard_error_envelope(client):
    """Any AppException returns { error: {code, message, details}, meta: {request_id, timestamp} }."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "wrong"},
    )
    assert response.status_code == 401
    body = response.json()

    # error block
    assert "error" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert isinstance(body["error"]["message"], str)
    assert isinstance(body["error"]["details"], list)

    # meta block
    assert "meta" in body
    assert "request_id" in body["meta"]
    assert body["meta"]["request_id"] is not None
    assert "timestamp" in body["meta"]


async def test_validation_error_returns_standard_envelope(client):
    """Pydantic 422 errors are re-formatted into standard error envelope."""
    # Send a login with missing required fields
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422
    body = response.json()

    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) > 0

    # Check detail structure
    detail = body["error"]["details"][0]
    assert "field" in detail
    assert "message" in detail
    assert "type" in detail

    # meta present
    assert "meta" in body
    assert "request_id" in body["meta"]
    assert "timestamp" in body["meta"]


async def test_request_id_header_set_on_response(client):
    """Middleware sets X-Request-ID on every response."""
    response = await client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


# ── Pagination helper ──────────────────────────────────────────


def test_pagination_params_defaults():
    from app.shared.pagination import PaginationParams

    p = PaginationParams()
    assert p.page == 1
    assert p.page_size == 20
    assert p.sort is None
    assert p.offset == 0


def test_pagination_params_offset():
    from app.shared.pagination import PaginationParams

    p = PaginationParams(page=3, page_size=10)
    assert p.offset == 20


def test_paginated_response_meta():
    from unittest.mock import MagicMock

    from app.shared.pagination import PaginationParams, paginated_response

    request = MagicMock()
    request.state.request_id = "test-req-123"

    pagination = PaginationParams(page=2, page_size=10)
    result = paginated_response(request, items=["a", "b"], total=25, pagination=pagination)

    assert result["data"] == ["a", "b"]
    assert result["meta"]["page"] == 2
    assert result["meta"]["page_size"] == 10
    assert result["meta"]["total"] == 25
    assert result["meta"]["total_pages"] == 3
    assert result["meta"]["request_id"] == "test-req-123"
    assert "timestamp" in result["meta"]


def test_paginated_response_total_pages_edge_cases():
    from unittest.mock import MagicMock

    from app.shared.pagination import PaginationParams, paginated_response

    request = MagicMock()
    request.state.request_id = None

    # Exact division
    p = PaginationParams(page=1, page_size=10)
    r = paginated_response(request, [], total=30, pagination=p)
    assert r["meta"]["total_pages"] == 3

    # One extra
    r = paginated_response(request, [], total=31, pagination=p)
    assert r["meta"]["total_pages"] == 4

    # Zero
    r = paginated_response(request, [], total=0, pagination=p)
    assert r["meta"]["total_pages"] == 0


# ── Success response wrapper ──────────────────────────────────


async def test_success_response_wrapper():
    from unittest.mock import MagicMock

    from app.shared.exceptions import success_response

    request = MagicMock()
    request.state.request_id = "req-42"

    resp = success_response(request, {"id": "abc"})
    assert resp.status_code == 200

    import json
    body = json.loads(resp.body)
    assert body["data"]["id"] == "abc"
    assert body["meta"]["request_id"] == "req-42"
    assert "timestamp" in body["meta"]


async def test_success_response_custom_status_and_headers():
    from unittest.mock import MagicMock

    from app.shared.exceptions import success_response

    request = MagicMock()
    request.state.request_id = "req-99"

    resp = success_response(request, {"ok": True}, status_code=201, headers={"ETag": '"5"'})
    assert resp.status_code == 201
    assert resp.headers.get("ETag") == '"5"'
