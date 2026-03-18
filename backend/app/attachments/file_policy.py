"""Upload policy enforcement for attachments (B06.11).

NFR-08a compliance: MIME whitelist, file size limits, rate limiting.
"""

from app.shared.exceptions import AttachmentPolicyViolation

# ── MIME whitelist ──
ALLOWED_MIME_TYPES: dict[str, int] = {
    # Images — 50 MB max
    "image/jpeg": 50 * 1024 * 1024,
    "image/png": 50 * 1024 * 1024,
    "image/webp": 50 * 1024 * 1024,
    "image/heic": 50 * 1024 * 1024,
    "image/heif": 50 * 1024 * 1024,
    # Videos — 500 MB max
    "video/mp4": 500 * 1024 * 1024,
    "video/quicktime": 500 * 1024 * 1024,
    "video/x-msvideo": 500 * 1024 * 1024,
    # PDF — 20 MB max
    "application/pdf": 20 * 1024 * 1024,
    # Excel/CSV — 20 MB max
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": 20 * 1024 * 1024,
    "application/wps-office.xlsx": 20 * 1024 * 1024,
    "text/csv": 20 * 1024 * 1024,
}


def validate_mime_type(mime_type: str) -> None:
    """Validate that mime_type is in the allowed whitelist."""
    if mime_type not in ALLOWED_MIME_TYPES:
        raise AttachmentPolicyViolation(
            f"MIME type '{mime_type}' không được hỗ trợ. "
            f"Cho phép: {', '.join(sorted(ALLOWED_MIME_TYPES.keys()))}"
        )


def validate_file_size(mime_type: str, file_size_bytes: int) -> None:
    """Validate that file size is within limits for the given MIME type."""
    if file_size_bytes <= 0:
        raise AttachmentPolicyViolation("File size phải > 0 bytes.")

    max_size = ALLOWED_MIME_TYPES.get(mime_type)
    if max_size and file_size_bytes > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size_bytes / (1024 * 1024)
        raise AttachmentPolicyViolation(
            f"File size {actual_mb:.1f}MB vượt giới hạn {max_mb:.0f}MB cho loại {mime_type}."
        )


def get_max_file_size(mime_type: str) -> int:
    """Return maximum file size in bytes for a given MIME type."""
    return ALLOWED_MIME_TYPES.get(mime_type, 50 * 1024 * 1024)
