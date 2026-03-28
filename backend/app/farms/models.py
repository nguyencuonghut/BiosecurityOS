"""ORM models for Farm sub-entities (Sprint 02)."""

import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RiskType(str, enum.Enum):
    MARKET = "market"
    DUMP = "dump"
    SLAUGHTERHOUSE = "slaughterhouse"
    DISPOSAL_SITE = "disposal_site"
    WASTEWATER = "wastewater"
    FARM = "farm"
    WATER_SOURCE = "water_source"
    ROAD = "road"
    OTHER = "other"


class AreaType(Base):
    __tablename__ = "area_type"
    __table_args__ = {"schema": "biosec"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

class FarmArea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farm_area"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="CASCADE"), nullable=False
    )
    parent_area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="SET NULL")
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.area_type.id", ondelete="RESTRICT"), nullable=False
    )
    clean_dirty_class: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)

    farm = relationship("Farm", back_populates="areas")
    parent = relationship("FarmArea", remote_side="FarmArea.id", backref="children")
    area_type_rel: Mapped["AreaType"] = relationship("AreaType", lazy="selectin")


class FarmRoute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farm_route"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="CASCADE"), nullable=False
    )
    route_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="RESTRICT"), nullable=False
    )
    to_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm_area.id", ondelete="RESTRICT"), nullable=False
    )
    direction_rule: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    farm = relationship("Farm", back_populates="routes")
    from_area = relationship("FarmArea", foreign_keys=[from_area_id])
    to_area = relationship("FarmArea", foreign_keys=[to_area_id])


class ExternalRiskPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_risk_point"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biosec.farm.id", ondelete="CASCADE"), nullable=False
    )
    risk_type: Mapped[RiskType] = mapped_column(
        SAEnum(RiskType, name="external_risk_point_risk_type_enum", schema="biosec",
               create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)

    farm = relationship("Farm", back_populates="external_risk_points")
