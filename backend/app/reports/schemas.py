"""Report schemas (B10.1-B10.3)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

VALID_REPORT_TYPES = [
    "monthly_biosecurity_summary",
    "farm_score_comparison",
    "case_backlog",
    "overdue_tasks",
    "killer_metrics_summary",
    "trust_gap_report",
    "scar_hotspot_report",
]

VALID_FORMATS = ["xlsx", "csv", "pdf"]


class ReportCreateRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")
    format: str = Field(default="xlsx", pattern=r"^(xlsx|csv|pdf)$")
    filters: dict | None = Field(default=None, description="Optional filters (month, region_id, farm_id, etc.)")


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requested_by: uuid.UUID
    report_type: str
    format: str
    filters: dict | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
