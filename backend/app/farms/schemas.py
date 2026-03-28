"""Pydantic schemas for Farm module (farm, area, route, external risk point)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.farms.models import RiskType


# ── Farm ────────────────────────────────────────────────────────

class FarmCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    farm_type: str = Field(pattern=r"^(sow|finisher|mixed|other)$")
    ownership_type: str = Field(pattern=r"^(company|lease|contract|other)$")
    region_id: uuid.UUID
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    capacity_headcount: int | None = Field(default=None, ge=0)
    operational_status: str = Field(default="active", pattern=r"^(active|paused|closed|archived)$")
    baseline_risk_level: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    structural_risk_note: str | None = None
    opened_at: date | None = None
    closed_at: date | None = None


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    farm_type: str | None = Field(default=None, pattern=r"^(sow|finisher|mixed|other)$")
    ownership_type: str | None = Field(default=None, pattern=r"^(company|lease|contract|other)$")
    region_id: uuid.UUID | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    capacity_headcount: int | None = Field(default=None, ge=0)
    operational_status: str | None = Field(default=None, pattern=r"^(active|paused|closed|archived)$")
    baseline_risk_level: str | None = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    structural_risk_note: str | None = None
    opened_at: date | None = None
    closed_at: date | None = None


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    farm_type: str
    ownership_type: str
    region_id: uuid.UUID
    address: str | None
    latitude: float | None
    longitude: float | None
    capacity_headcount: int | None
    operational_status: str
    baseline_risk_level: str
    structural_risk_note: str | None
    opened_at: date | None
    closed_at: date | None
    created_at: datetime
    updated_at: datetime


# ── Farm Area ───────────────────────────────────────────────────

class AreaCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    area_type: str = Field(max_length=50)
    parent_area_id: uuid.UUID | None = None
    clean_dirty_class: str | None = Field(default=None, pattern=r"^(clean|buffer|dirty)$")
    is_active: bool = True


class AreaUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    area_type: str | None = Field(default=None, max_length=50)
    parent_area_id: uuid.UUID | None = None
    clean_dirty_class: str | None = Field(default=None, pattern=r"^(clean|buffer|dirty)$")
    is_active: bool | None = None


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    parent_area_id: uuid.UUID | None
    code: str
    name: str
    area_type: str
    clean_dirty_class: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Farm Route ──────────────────────────────────────────────────

class RouteCreate(BaseModel):
    route_type: str = Field(max_length=30)
    from_area_id: uuid.UUID
    to_area_id: uuid.UUID
    direction_rule: str = Field(pattern=r"^(one_way|restricted|conditional|bidirectional)$")
    note: str | None = None


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    route_type: str
    from_area_id: uuid.UUID
    to_area_id: uuid.UUID
    direction_rule: str
    note: str | None
    created_at: datetime
    updated_at: datetime


# ── External Risk Point ─────────────────────────────────────────

RISK_TYPE_LABELS: dict[RiskType, str] = {
    RiskType.MARKET: "Chợ gia súc",
    RiskType.DUMP: "Bãi rác",
    RiskType.SLAUGHTERHOUSE: "Lò mổ",
    RiskType.DISPOSAL_SITE: "Khu tiêu hủy",
    RiskType.WASTEWATER: "Ao nước thải",
    RiskType.FARM: "Trại chăn nuôi lân cận",
    RiskType.WATER_SOURCE: "Nguồn nước",
    RiskType.ROAD: "Đường giao thông lớn",
    RiskType.OTHER: "Khác",
}


class ExternalRiskPointCreate(BaseModel):
    risk_type: RiskType
    name: str | None = Field(default=None, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    distance_m: int | None = Field(default=None, ge=0)
    note: str | None = None
    confidence_level: str = Field(pattern=r"^(suspected|probable|confirmed)$")


class ExternalRiskPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    risk_type: RiskType
    name: str | None
    latitude: float
    longitude: float
    distance_m: int | None
    note: str | None
    confidence_level: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def risk_type_label(self) -> str:
        return RISK_TYPE_LABELS.get(self.risk_type, self.risk_type.value)
