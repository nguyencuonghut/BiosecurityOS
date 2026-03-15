"""Tests for B01.9 — Optimistic lock utility."""

import pytest

from app.shared.exceptions import ConflictException, ValidationException
from app.shared.optimistic_lock import (
    apply_version_update,
    check_version,
    etag_headers,
    parse_if_match,
    require_if_match,
)


# ── check_version ──────────────────────────────────────────────


def test_check_version_passes_when_equal():
    check_version(3, 3)  # should not raise


def test_check_version_raises_409_on_mismatch():
    with pytest.raises(ConflictException) as exc_info:
        check_version(current_version=5, expected_version=3)
    assert exc_info.value.status_code == 409
    assert "version 3" in exc_info.value.message
    assert "version is 5" in exc_info.value.message


# ── apply_version_update ──────────────────────────────────────


def test_apply_version_update():
    assert apply_version_update(1) == 2
    assert apply_version_update(99) == 100


# ── etag_headers ──────────────────────────────────────────────


def test_etag_headers_format():
    h = etag_headers(7)
    assert h == {"ETag": '"7"'}


def test_etag_headers_with_version_1():
    h = etag_headers(1)
    assert h["ETag"] == '"1"'


# ── parse_if_match ────────────────────────────────────────────


def test_parse_if_match_none():
    assert parse_if_match(None) is None


def test_parse_if_match_plain_number():
    assert parse_if_match("5") == 5


def test_parse_if_match_quoted():
    assert parse_if_match('"12"') == 12


def test_parse_if_match_whitespace():
    assert parse_if_match('  "3"  ') == 3


def test_parse_if_match_invalid():
    assert parse_if_match("abc") is None
    assert parse_if_match("") is None


# ── require_if_match ──────────────────────────────────────────


def test_require_if_match_returns_version():
    assert require_if_match("5") == 5
    assert require_if_match('"10"') == 10


def test_require_if_match_raises_on_none():
    with pytest.raises(ValidationException) as exc_info:
        require_if_match(None)
    assert exc_info.value.status_code == 422
    assert "If-Match" in exc_info.value.message


def test_require_if_match_raises_on_invalid():
    with pytest.raises(ValidationException) as exc_info:
        require_if_match("not-a-number")
    assert exc_info.value.status_code == 422
    assert "Invalid" in exc_info.value.message
