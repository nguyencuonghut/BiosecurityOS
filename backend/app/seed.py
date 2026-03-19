"""Comprehensive seed script: creates sample data for all modules.

Builds a realistic demo environment with regions, farms, scorecards,
assessments, killer events, trust scores, cases, RCA, tasks, etc.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AppRole, AppUser, AppUserCredential, UserRole, Farm, Region
from app.auth.security import hash_password
from app.database import async_session_factory

# Import all models so SQLAlchemy relationship registry is complete
import app.farms.models  # noqa: F401
import app.scorecards.models  # noqa: F401
import app.assessments.models  # noqa: F401
import app.killer_metrics.models  # noqa: F401
import app.trust_scores.models  # noqa: F401
import app.cases.models  # noqa: F401
import app.tasks.models  # noqa: F401
import app.attachments.models  # noqa: F401
import app.floorplans.models  # noqa: F401
import app.scars.models  # noqa: F401
import app.lessons.models  # noqa: F401

from app.farms.models import FarmArea, FarmRoute, ExternalRiskPoint
from app.scorecards.models import ScorecardTemplate, ScorecardSection, ScorecardItem
from app.assessments.models import Assessment
from app.killer_metrics.models import KillerMetricDefinition, KillerMetricEvent
from app.trust_scores.models import TrustScoreSnapshot
from app.cases.models import RiskCase, CaseParticipant, RcaRecord, RcaFactor
from app.tasks.models import CorrectiveTask, TaskAssignee, TaskReview, TaskComment
from app.floorplans.models import FloorplanVersion, FloorplanMarker
from app.scars.models import ScarRecord, ScarLink
from app.lessons.models import LessonLearned, LessonReference, SimilarityTag

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

DEFAULT_PASSWORD = "Admin@2026"
NOW = datetime.now(timezone.utc)

SEED_USERS = [
    ("admin", "System Administrator", "admin@biosec.local", "SYSTEM_ADMIN"),
    ("region_mgr", "Nguyễn Văn Vùng", "region_mgr@biosec.local", "REGION_MANAGER"),
    ("farm_mgr", "Trần Thị Trại", "farm_mgr@biosec.local", "FARM_MANAGER"),
    ("expert", "Lê Văn Chuyên", "expert@biosec.local", "BIOSEC_EXPERT"),
    ("auditor", "Phạm Thị Kiểm", "auditor@biosec.local", "AUDITOR"),
    ("viewer", "Hoàng Văn Xem", "viewer@biosec.local", "VIEWER"),
]


# ═══════════════════════════════════════════════════════════════
# 1. Users
# ═══════════════════════════════════════════════════════════════

async def seed_users(db: AsyncSession | None = None) -> dict[str, AppUser]:
    """Create test users. Can be called standalone or as part of seed_all."""
    standalone = db is None
    if standalone:
        db = async_session_factory()
        await db.__aenter__()

    users = {}
    for username, full_name, email, role_code in SEED_USERS:
        result = await db.execute(select(AppUser).where(AppUser.username == username))
        existing = result.scalar_one_or_none()
        if existing:
            users[username] = existing
            print(f"  User '{username}' already exists, skipping.")
            continue

        user = AppUser(username=username, full_name=full_name, email=email, status="active")
        db.add(user)
        await db.flush()

        db.add(AppUserCredential(user_id=user.id, password_hash=hash_password(DEFAULT_PASSWORD)))

        role_result = await db.execute(select(AppRole).where(AppRole.code == role_code))
        role = role_result.scalar_one_or_none()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))

        users[username] = user
        print(f"  Created user: {username} / {role_code}")

    if standalone:
        await db.commit()
        await db.__aexit__(None, None, None)

    return users


# ═══════════════════════════════════════════════════════════════
# 2. Regions & Farms
# ═══════════════════════════════════════════════════════════════

SEED_REGIONS = [
    ("REG-NORTH", "Vùng Bắc"),
    ("REG-CENTRAL", "Vùng Trung"),
    ("REG-SOUTH", "Vùng Nam"),
]

SEED_FARMS = [
    # (code, name, farm_type, ownership_type, region_code, capacity, risk_level, lat, lon, address)
    ("FARM-N01", "Trại Hà Nam 1", "sow", "company", "REG-NORTH", 5000, "medium", 20.5833, 106.0000, "Xã Liêm Thuận, Thanh Liêm, Hà Nam"),
    ("FARM-N02", "Trại Bắc Ninh 1", "finisher", "company", "REG-NORTH", 8000, "low", 21.1861, 106.0763, "Xã Phú Lâm, Tiên Du, Bắc Ninh"),
    ("FARM-N03", "Trại Thái Bình 1", "mixed", "contract", "REG-NORTH", 3000, "high", 20.4500, 106.3333, "Xã Thụy Trường, Thái Thụy, Thái Bình"),
    ("FARM-C01", "Trại Thanh Hóa 1", "sow", "company", "REG-CENTRAL", 6000, "medium", 19.8000, 105.7667, "Xã Hoằng Quỳ, Hoằng Hóa, Thanh Hóa"),
    ("FARM-C02", "Trại Nghệ An 1", "finisher", "lease", "REG-CENTRAL", 4000, "medium", 18.6700, 105.6900, "Xã Nghi Long, Nghi Lộc, Nghệ An"),
    ("FARM-S01", "Trại Đồng Nai 1", "sow", "company", "REG-SOUTH", 10000, "low", 10.9500, 106.8500, "Xã Sông Trầu, Trảng Bom, Đồng Nai"),
    ("FARM-S02", "Trại Bình Dương 1", "mixed", "company", "REG-SOUTH", 7000, "medium", 11.3254, 106.4770, "Xã An Bình, Phú Giáo, Bình Dương"),
    ("FARM-S03", "Trại Long An 1", "finisher", "contract", "REG-SOUTH", 5000, "high", 10.5333, 106.4167, "Xã Đức Hòa Thượng, Đức Hòa, Long An"),
]

SEED_AREAS = [
    ("GATE", "Cổng chính", "gate", "dirty"),
    ("CLEAN", "Khu sạch", "production", "clean"),
    ("BUFFER", "Khu đệm", "buffer", "buffer"),
    ("DIRTY", "Khu bẩn", "logistics", "dirty"),
    ("OFFICE", "Văn phòng", "office", None),
    ("QUARANTINE", "Khu cách ly", "quarantine", "clean"),
    ("SHOWER", "Nhà tắm sát trùng", "buffer_zone", "buffer"),
    ("FEED_STORE", "Kho cám", "storage", "dirty"),
    ("DEAD_PIG", "Khu xử lý heo chết", "yard", "dirty"),
]


async def _seed_regions_and_farms(db: AsyncSession, users: dict) -> tuple:
    regions, farms, areas = {}, {}, {}

    for code, name in SEED_REGIONS:
        result = await db.execute(select(Region).where(Region.code == code))
        existing = result.scalar_one_or_none()
        if existing:
            regions[code] = existing
            continue
        region = Region(code=code, name=name, manager_user_id=users["region_mgr"].id, status="active")
        db.add(region)
        regions[code] = region
        print(f"  Created region: {code}")
    await db.flush()

    for code, name, farm_type, ownership, region_code, capacity, risk, lat, lon, address in SEED_FARMS:
        result = await db.execute(select(Farm).where(Farm.code == code))
        existing = result.scalar_one_or_none()
        if existing:
            farms[code] = existing
            continue
        farm = Farm(
            code=code, name=name, farm_type=farm_type, ownership_type=ownership,
            region_id=regions[region_code].id,
            capacity_headcount=capacity, baseline_risk_level=risk,
            latitude=Decimal(str(lat)), longitude=Decimal(str(lon)),
            address=address, operational_status="active", opened_at=date(2024, 1, 15),
        )
        db.add(farm)
        farms[code] = farm
        print(f"  Created farm: {code} — {name}")
    await db.flush()

    for farm_code, farm in farms.items():
        for suffix, area_name, area_type, cdc in SEED_AREAS:
            area_code = f"{farm_code}-{suffix}"
            result = await db.execute(select(FarmArea).where(FarmArea.code == area_code))
            if result.scalar_one_or_none():
                continue
            area = FarmArea(
                farm_id=farm.id, code=area_code, name=area_name,
                area_type=area_type, clean_dirty_class=cdc, is_active=True,
            )
            db.add(area)
            areas[(farm_code, suffix)] = area
    await db.flush()

    for farm_code, farm in farms.items():
        gate = areas.get((farm_code, "GATE"))
        clean = areas.get((farm_code, "CLEAN"))
        buffer = areas.get((farm_code, "BUFFER"))
        dirty = areas.get((farm_code, "DIRTY"))
        shower = areas.get((farm_code, "SHOWER"))
        feed_store = areas.get((farm_code, "FEED_STORE"))
        dead_pig = areas.get((farm_code, "DEAD_PIG"))
        quarantine = areas.get((farm_code, "QUARANTINE"))
        if clean and buffer and dirty:
            # Vehicle routes: dirty → buffer → clean (one way)
            for from_a, to_a in [(dirty, buffer), (buffer, clean)]:
                db.add(FarmRoute(
                    farm_id=farm.id, route_type="vehicle",
                    from_area_id=from_a.id, to_area_id=to_a.id,
                    direction_rule="one_way",
                    note="Chỉ di chuyển một chiều từ bẩn → sạch",
                ))
        if gate and shower:
            # Person route: gate → shower → buffer → clean
            db.add(FarmRoute(
                farm_id=farm.id, route_type="person",
                from_area_id=gate.id, to_area_id=shower.id,
                direction_rule="one_way",
                note="Người vào trại phải qua nhà tắm sát trùng",
            ))
        if shower and buffer:
            db.add(FarmRoute(
                farm_id=farm.id, route_type="person",
                from_area_id=shower.id, to_area_id=buffer.id,
                direction_rule="one_way",
                note="Sau khi tắm sát trùng, vào khu đệm",
            ))
        if buffer and clean:
            db.add(FarmRoute(
                farm_id=farm.id, route_type="person",
                from_area_id=buffer.id, to_area_id=clean.id,
                direction_rule="one_way",
                note="Từ khu đệm vào khu sạch",
            ))
        if dead_pig and dirty:
            # Deadstock route: clean → dead_pig zone (one way)
            db.add(FarmRoute(
                farm_id=farm.id, route_type="deadstock",
                from_area_id=clean.id, to_area_id=dead_pig.id,
                direction_rule="one_way",
                note="Xác chết chỉ di chuyển ra ngoài, không quay lại",
            ))
        if feed_store and buffer:
            # Feed route: feed_store → buffer (restricted)
            db.add(FarmRoute(
                farm_id=farm.id, route_type="feed",
                from_area_id=feed_store.id, to_area_id=buffer.id,
                direction_rule="restricted",
                note="Cám chỉ được vận chuyển qua khu đệm sau khi sát trùng",
            ))

    for farm_code in ["FARM-N03", "FARM-S03"]:
        farm = farms.get(farm_code)
        if not farm:
            continue
        db.add(ExternalRiskPoint(
            farm_id=farm.id, risk_type="market",
            name="Chợ gia súc lân cận", latitude=farm.latitude + Decimal("0.01"),
            longitude=farm.longitude + Decimal("0.01"), distance_m=800,
            note="Chợ buôn bán gia súc, hoạt động hàng tuần", confidence_level="confirmed",
        ))
        db.add(ExternalRiskPoint(
            farm_id=farm.id, risk_type="dump",
            name="Bãi rác lộ thiên", latitude=farm.latitude - Decimal("0.005"),
            longitude=farm.longitude + Decimal("0.008"), distance_m=1200,
            note="Bãi rác có nguy cơ thu hút động vật gây bệnh", confidence_level="probable",
        ))
    await db.flush()
    print(f"  Created {len(areas)} farm areas, routes, risk points")
    return regions, farms, areas


# ═══════════════════════════════════════════════════════════════
# 3. Scorecard Templates
# ═══════════════════════════════════════════════════════════════

SCORECARD_SECTIONS = [
    ("HW", "Hạ tầng & cơ sở vật chất", "hardware", Decimal("30"), 1),
    ("PR", "Quy trình & SOP", "software", Decimal("30"), 2),
    ("BH", "Hành vi & tuân thủ", "behavior", Decimal("25"), 3),
    ("MN", "Giám sát & cảnh báo", "monitoring", Decimal("15"), 4),
]

ITEMS_PER_SECTION = {
    "HW": [
        ("Hàng rào bao quanh trại nguyên vẹn", "yes_no", 10, False),
        ("Cổng ra vào có khóa & kiểm soát", "yes_no", 10, False),
        ("Khu cách ly đúng quy cách", "score_0_5", 10, False),
        ("Hệ thống sát trùng xe tải hoạt động", "yes_no", 10, True),
        ("Kho chứa cám cách ly đúng cách", "score_0_5", 10, False),
    ],
    "PR": [
        ("SOP tiếp nhận heo mới", "yes_no", 10, False),
        ("SOP xử lý heo chết", "yes_no", 10, True),
        ("Lịch sát trùng định kỳ", "score_0_5", 10, False),
        ("Quy trình kiểm tra sức khỏe hàng ngày", "score_0_5", 10, False),
        ("SOP quản lý khách/xe ra vào", "yes_no", 10, False),
    ],
    "BH": [
        ("Nhân viên thay đồ trước khi vào khu sạch", "yes_no", 10, False),
        ("Tắm sát trùng trước khi vào chuồng", "yes_no", 10, True),
        ("Không mang thức ăn bên ngoài vào trại", "yes_no", 10, True),
        ("Ghi chép đầy đủ sổ theo dõi ATSH", "score_0_5", 10, False),
    ],
    "MN": [
        ("Camera giám sát hoạt động 24/7", "yes_no", 10, False),
        ("Hệ thống cảnh báo nhiệt độ/ẩm độ", "score_0_5", 10, False),
        ("Báo cáo ATSH hàng tuần", "yes_no", 10, False),
    ],
}


async def _seed_scorecards(db: AsyncSession) -> dict:
    templates = {}
    TEMPLATES = [
        ("SC-SOW-V1", "Scorecard ATSH — Trại nái", "sow", 1),
        ("SC-FIN-V1", "Scorecard ATSH — Trại thịt", "finisher", 1),
        ("SC-MIX-V1", "Scorecard ATSH — Trại hỗn hợp", "mixed", 1),
    ]
    for t_code, t_name, farm_type, ver in TEMPLATES:
        result = await db.execute(select(ScorecardTemplate).where(ScorecardTemplate.code == t_code))
        existing = result.scalar_one_or_none()
        if existing:
            templates[t_code] = existing
            continue

        template = ScorecardTemplate(
            code=t_code, name=t_name, farm_type=farm_type,
            version_no=ver, status="active", effective_from=date(2026, 1, 1),
        )
        db.add(template)
        await db.flush()
        templates[t_code] = template

        for s_suffix, s_name, s_type, s_weight, s_order in SCORECARD_SECTIONS:
            section = ScorecardSection(
                template_id=template.id, code=f"{t_code}-{s_suffix}", name=s_name,
                section_type=s_type, weight=s_weight, display_order=s_order,
            )
            db.add(section)
            await db.flush()

            for idx, (q_text, resp_type, max_score, is_killer) in enumerate(ITEMS_PER_SECTION.get(s_suffix, []), 1):
                db.add(ScorecardItem(
                    section_id=section.id, code=f"{t_code}-{s_suffix}-{idx:02d}",
                    question_text=q_text, response_type=resp_type,
                    max_score=Decimal(str(max_score)), weight=Decimal("1"),
                    is_killer_related=is_killer, display_order=idx,
                ))

        print(f"  Created scorecard: {t_code}")
    await db.flush()
    return templates


# ═══════════════════════════════════════════════════════════════
# 4. Assessments
# ═══════════════════════════════════════════════════════════════

FARM_TEMPLATE_MAP = {"sow": "SC-SOW-V1", "finisher": "SC-FIN-V1", "mixed": "SC-MIX-V1"}

ASSESSMENT_DATA = [
    # Current round (14 days ago)
    ("FARM-N01", "self", "farm_mgr", "78.5", "82", "75", "80", "76", 14),
    ("FARM-N01", "scheduled_audit", "auditor", "72.0", "78", "68", "74", "66", 14),
    ("FARM-N02", "self", "farm_mgr", "85.0", "88", "82", "86", "82", 14),
    ("FARM-N02", "scheduled_audit", "auditor", "80.5", "84", "78", "82", "76", 14),
    ("FARM-N03", "self", "farm_mgr", "45.0", "50", "40", "48", "40", 14),
    ("FARM-N03", "scheduled_audit", "auditor", "38.0", "42", "34", "40", "34", 14),
    ("FARM-C01", "self", "farm_mgr", "65.0", "70", "60", "68", "60", 14),
    ("FARM-C01", "scheduled_audit", "auditor", "55.0", "62", "50", "58", "48", 14),
    ("FARM-C02", "self", "farm_mgr", "70.0", "74", "66", "72", "66", 14),
    ("FARM-C02", "scheduled_audit", "auditor", "66.0", "70", "62", "68", "62", 14),
    ("FARM-S01", "self", "farm_mgr", "90.0", "92", "88", "90", "90", 14),
    ("FARM-S01", "scheduled_audit", "auditor", "88.0", "90", "86", "88", "88", 14),
    ("FARM-S02", "self", "farm_mgr", "75.0", "78", "72", "76", "72", 14),
    ("FARM-S02", "scheduled_audit", "auditor", "71.0", "74", "68", "72", "68", 14),
    ("FARM-S03", "self", "farm_mgr", "50.0", "55", "45", "52", "46", 14),
    ("FARM-S03", "scheduled_audit", "auditor", "42.0", "48", "38", "44", "36", 14),
    # 3 months ago
    ("FARM-N01", "self", "farm_mgr", "72.0", "76", "68", "74", "68", 90),
    ("FARM-N01", "scheduled_audit", "auditor", "65.0", "70", "60", "68", "60", 90),
    ("FARM-N02", "self", "farm_mgr", "80.0", "82", "78", "82", "76", 90),
    ("FARM-C01", "self", "farm_mgr", "58.0", "64", "52", "60", "54", 90),
    ("FARM-C01", "scheduled_audit", "auditor", "48.0", "54", "42", "50", "44", 90),
    ("FARM-S01", "self", "farm_mgr", "86.0", "88", "84", "86", "86", 90),
    ("FARM-S01", "scheduled_audit", "auditor", "84.0", "86", "82", "84", "84", 90),
    ("FARM-S03", "self", "farm_mgr", "44.0", "50", "38", "46", "40", 90),
    ("FARM-S03", "scheduled_audit", "auditor", "36.0", "42", "30", "38", "32", 90),
    # 6 months ago
    ("FARM-N01", "self", "farm_mgr", "68.0", "72", "64", "70", "64", 180),
    ("FARM-N01", "scheduled_audit", "auditor", "60.0", "64", "56", "62", "56", 180),
    ("FARM-N02", "self", "farm_mgr", "76.0", "78", "74", "78", "72", 180),
    ("FARM-C01", "self", "farm_mgr", "52.0", "58", "46", "54", "48", 180),
    ("FARM-S01", "self", "farm_mgr", "82.0", "84", "80", "82", "82", 180),
    ("FARM-S01", "scheduled_audit", "auditor", "80.0", "82", "78", "80", "80", 180),
    ("FARM-S03", "self", "farm_mgr", "40.0", "46", "34", "42", "36", 180),
    ("FARM-S03", "scheduled_audit", "auditor", "32.0", "38", "26", "34", "28", 180),
    # 9 months ago
    ("FARM-N01", "self", "farm_mgr", "62.0", "66", "58", "64", "58", 270),
    ("FARM-S01", "self", "farm_mgr", "78.0", "80", "76", "78", "78", 270),
    ("FARM-S03", "self", "farm_mgr", "35.0", "40", "30", "36", "32", 270),
]


async def _seed_assessments(db: AsyncSession, farms: dict, templates: dict, users: dict) -> dict:
    assessments = {}
    for farm_code, a_type, performer, overall, hw, pr, bh, mn, days_ago in ASSESSMENT_DATA:
        farm = farms.get(farm_code)
        if not farm:
            continue
        t_code = FARM_TEMPLATE_MAP.get(farm.farm_type)
        template = templates.get(t_code)
        if not template:
            continue

        key = f"{farm_code}_{a_type}_{days_ago}"
        assess = Assessment(
            farm_id=farm.id, template_id=template.id, assessment_type=a_type,
            assessment_date=NOW - timedelta(days=days_ago),
            performed_by_user_id=users[performer].id,
            performed_by_name_snapshot=users[performer].full_name,
            overall_score=Decimal(overall), hardware_score=Decimal(hw),
            process_score=Decimal(pr), behavior_score=Decimal(bh),
            monitoring_score=Decimal(mn), status="reviewed",
            summary_note=f"Đánh giá {a_type} cho {farm.name}",
        )
        db.add(assess)
        assessments[key] = assess

    await db.flush()
    print(f"  Created {len(assessments)} assessments")
    return assessments


# ═══════════════════════════════════════════════════════════════
# 5. Trust Scores
# ═══════════════════════════════════════════════════════════════

async def _seed_trust_scores(db: AsyncSession, farms: dict, assessments: dict) -> None:
    count = 0
    # Multiple snapshots — each needs matching self + audit assessments
    # Use (farm_code, days_ago_for_assessment) pairs based on ASSESSMENT_DATA
    TRUST_DATA = [
        # (farm_code, trust_score, gap, snapshot_days_ago, assessment_days_ago)
        # Current round — assessments at day 14
        ("FARM-N01", Decimal("87"), Decimal("6.5"), 0, 14),
        ("FARM-N02", Decimal("91"), Decimal("4.5"), 0, 14),
        ("FARM-N03", Decimal("42"), Decimal("29"), 0, 14),
        ("FARM-C01", Decimal("58"), Decimal("21"), 0, 14),
        ("FARM-C02", Decimal("72"), Decimal("14"), 0, 14),
        ("FARM-S01", Decimal("96"), Decimal("2"), 0, 14),
        ("FARM-S02", Decimal("78"), Decimal("11"), 0, 14),
        ("FARM-S03", Decimal("34"), Decimal("33"), 0, 14),
        # 3 months ago — only farms with audit at 90 days
        ("FARM-N01", Decimal("82"), Decimal("9"), 90, 90),
        ("FARM-S01", Decimal("94"), Decimal("3"), 90, 90),
        ("FARM-C01", Decimal("50"), Decimal("25"), 90, 90),
        ("FARM-S03", Decimal("30"), Decimal("35"), 90, 90),
        # 6 months ago
        ("FARM-N01", Decimal("76"), Decimal("12"), 180, 180),
        ("FARM-S01", Decimal("92"), Decimal("4"), 180, 180),
        ("FARM-S03", Decimal("26"), Decimal("37"), 180, 180),
    ]
    for farm_code, trust, gap, snap_days, assess_days in TRUST_DATA:
        farm = farms.get(farm_code)
        if not farm:
            continue
        self_a = assessments.get(f"{farm_code}_self_{assess_days}")
        audit_a = assessments.get(f"{farm_code}_scheduled_audit_{assess_days}")
        if not self_a or not audit_a:
            continue
        db.add(TrustScoreSnapshot(
            farm_id=farm.id,
            source_self_assessment_id=self_a.id,
            source_audit_assessment_id=audit_a.id,
            trust_score=trust, absolute_gap_score=gap,
            snapshot_date=date.today() - timedelta(days=snap_days),
            note=f"Trust score for {farm.name}",
        ))
        count += 1
    await db.flush()
    print(f"  Created {count} trust score snapshots")


# ═══════════════════════════════════════════════════════════════
# 6. Killer Metric Events
# ═══════════════════════════════════════════════════════════════

async def _seed_killer_events(db: AsyncSession, farms: dict, areas: dict, users: dict) -> list:
    result = await db.execute(select(KillerMetricDefinition))
    defs = {d.code: d for d in result.scalars().all()}

    events = []
    EVENTS = [
        # (farm_code, area_suffix, def_code, detector, summary, days_ago, status)
        # Current month
        ("FARM-N03", "CLEAN", "SWILL_FEED", "expert", "Phát hiện thức ăn thừa không rõ nguồn gốc trong khu sạch", 3, "open"),
        ("FARM-S03", "DIRTY", "RED_LINE_BREACH", "farm_mgr", "Xe tải vào khu bẩn không qua sát trùng", 5, "open"),
        ("FARM-C01", "BUFFER", "DEAD_PIG_PROTOCOL_BREACH", "expert", "Heo chết không được xử lý đúng quy trình trong 4h", 7, "open"),
        ("FARM-N01", "DIRTY", "UNKNOWN_VISITOR", "farm_mgr", "Người lạ vào khu vực trại không đăng ký", 10, "under_review"),
        # 1 month ago
        ("FARM-S03", "CLEAN", "SWILL_FEED", "expert", "Nhân viên mang đồ ăn ngoài vào khu sạch", 35, "contained"),
        ("FARM-N03", "GATE", "UNKNOWN_VISITOR", "farm_mgr", "Xe lạ không đăng ký vào cổng trại", 40, "contained"),
        ("FARM-C01", "DIRTY", "RED_LINE_BREACH", "expert", "Nhân viên đi tắt qua khu bẩn không thay đồ", 42, "contained"),
        # 2 months ago
        ("FARM-S03", "DIRTY", "RED_LINE_BREACH", "farm_mgr", "Vi phạm vùng đỏ lần 2 — xe cám không sát trùng", 65, "contained"),
        ("FARM-N03", "BUFFER", "DEAD_PIG_PROTOCOL_BREACH", "expert", "Xác heo chết để quá 6h trong khu đệm", 70, "contained"),
        ("FARM-S02", "CLEAN", "SWILL_FEED", "farm_mgr", "Phát hiện thức ăn thừa gần chuồng nái", 75, "contained"),
        # 3 months ago
        ("FARM-N03", "DIRTY", "RED_LINE_BREACH", "expert", "Xe vận chuyển không qua hố sát trùng", 95, "contained"),
        ("FARM-C01", "CLEAN", "UNKNOWN_VISITOR", "farm_mgr", "Kỹ thuật viên bên ngoài vào khu sạch không tắm", 100, "contained"),
        # 4 months ago
        ("FARM-S03", "BUFFER", "DEAD_PIG_PROTOCOL_BREACH", "expert", "Vi phạm quy trình xử lý xác - chở ra ngoài", 125, "contained"),
        ("FARM-N01", "GATE", "UNKNOWN_VISITOR", "farm_mgr", "Người bán hàng rong vào khu vực cổng trại", 130, "contained"),
        # 5 months ago
        ("FARM-N03", "CLEAN", "SWILL_FEED", "expert", "Thức ăn thừa từ nhà bếp đổ sát khu chăn nuôi", 155, "contained"),
        ("FARM-S03", "DIRTY", "RED_LINE_BREACH", "farm_mgr", "Xe máy nhân viên vào khu bẩn không rửa", 160, "contained"),
    ]
    for farm_code, area_suffix, def_code, detector, summary, days_ago, status in EVENTS:
        farm = farms.get(farm_code)
        area = areas.get((farm_code, area_suffix))
        defn = defs.get(def_code)
        if not farm or not defn:
            continue
        event = KillerMetricEvent(
            farm_id=farm.id, area_id=area.id if area else None,
            definition_id=defn.id,
            event_at=NOW - timedelta(days=days_ago),
            detected_by_user_id=users[detector].id,
            source_type="manual", summary=summary, status=status,
        )
        db.add(event)
        events.append(event)
    await db.flush()
    print(f"  Created {len(events)} killer metric events")
    return events


# ═══════════════════════════════════════════════════════════════
# 7. Risk Cases & RCA
# ═══════════════════════════════════════════════════════════════

CASE_DATA = [
    ("RC-2026-001", "FARM-N03", "Sự cố thức ăn lạ khu sạch", "killer_event", "P0", "critical", "in_analysis"),
    ("RC-2026-002", "FARM-S03", "Vi phạm vùng đỏ — xe không sát trùng", "killer_event", "P0", "critical", "actioning"),
    ("RC-2026-003", "FARM-C01", "Vi phạm quy trình xử lý heo chết", "killer_event", "P0", "critical", "open"),
    ("RC-2026-004", "FARM-N01", "Người lạ xâm nhập khu vực trại", "killer_event", "P1", "high", "monitoring"),
    ("RC-2026-005", "FARM-C01", "Điểm ATSH thấp — quy trình yếu", "assessment_gap", "P2", "medium", "triage"),
    ("RC-2026-006", "FARM-S03", "Điểm trust score thấp — gap lớn", "trust_gap", "P1", "high", "in_analysis"),
]


async def _seed_cases(db: AsyncSession, farms: dict, users: dict) -> dict:
    cases = {}
    for case_no, farm_code, title, c_type, priority, severity, status in CASE_DATA:
        farm = farms.get(farm_code)
        if not farm:
            continue
        case = RiskCase(
            farm_id=farm.id, case_no=case_no, case_type=c_type,
            title=title, summary=f"Case demo: {title}",
            priority=priority, severity=severity, current_status=status,
            assigned_expert_user_id=users["expert"].id,
            first_response_due_at=NOW + timedelta(hours=4) if priority == "P0" else NOW + timedelta(days=1),
            closure_due_at=NOW + timedelta(days=7) if priority in ("P0", "P1") else NOW + timedelta(days=14),
        )
        db.add(case)
        cases[case_no] = case
    await db.flush()

    for case in cases.values():
        db.add(CaseParticipant(case_id=case.id, user_id=users["expert"].id, role_in_case="owner"))
        db.add(CaseParticipant(case_id=case.id, user_id=users["farm_mgr"].id, role_in_case="farm_contact"))
    await db.flush()

    for case_no in ["RC-2026-001", "RC-2026-002", "RC-2026-006"]:
        case = cases.get(case_no)
        if not case:
            continue
        rca = RcaRecord(
            case_id=case.id, method="5_why",
            problem_statement=f"Phân tích nguyên nhân gốc rễ cho {case.title}",
            direct_cause="Thiếu kiểm soát tại điểm ra vào",
            system_cause="SOP chưa được cập nhật đúng chu kỳ",
            behavioral_cause="Nhân viên chưa được đào tạo lại",
            conclusion_confidence="high",
            analyzed_by_user_id=users["expert"].id,
        )
        db.add(rca)
        await db.flush()
        db.add(RcaFactor(
            rca_record_id=rca.id, factor_group="process",
            factor_text="SOP kiểm soát ra vào chưa cập nhật quy trình mới",
            confidence_level="high", is_primary=True,
        ))
        db.add(RcaFactor(
            rca_record_id=rca.id, factor_group="people",
            factor_text="Nhân viên bảo vệ bỏ vị trí trong giờ nghỉ trưa",
            confidence_level="medium", is_primary=False,
        ))
    await db.flush()
    print(f"  Created {len(cases)} risk cases with participants, RCA")
    return cases


# ═══════════════════════════════════════════════════════════════
# 8. Corrective Tasks
# ═══════════════════════════════════════════════════════════════

TASK_DATA = [
    ("TASK-2026-001", "RC-2026-001", "Lắp camera giám sát khu sạch", "corrective", "P0", "in_progress", "farm_mgr"),
    ("TASK-2026-002", "RC-2026-001", "Cập nhật SOP kiểm soát thức ăn", "preventive", "P1", "open", "expert"),
    ("TASK-2026-003", "RC-2026-002", "Sửa chữa hệ thống sát trùng xe", "corrective", "P0", "pending_review", "farm_mgr"),
    ("TASK-2026-004", "RC-2026-002", "Đào tạo lại nhân viên bảo vệ", "preventive", "P1", "accepted", "farm_mgr"),
    ("TASK-2026-005", "RC-2026-003", "Xây dựng SOP xử lý heo chết mới", "corrective", "P0", "open", "expert"),
    ("TASK-2026-006", "RC-2026-004", "Lắp đặt barrier tự động cổng vào", "corrective", "P1", "closed", "farm_mgr"),
    ("TASK-2026-007", "RC-2026-005", "Nâng cấp hạ tầng sát trùng khu đệm", "corrective", "P2", "open", "farm_mgr"),
    ("TASK-2026-008", "RC-2026-006", "Kiểm tra chéo tự đánh giá và audit", "preventive", "P1", "in_progress", "auditor"),
    ("TASK-2026-009", "RC-2026-003", "Mua thiết bị tiêu hủy xác heo", "corrective", "P1", "open", "farm_mgr"),
    ("TASK-2026-010", "RC-2026-001", "Huấn luyện nhân viên về ATSH thức ăn", "preventive", "P2", "open", "farm_mgr"),
]


async def _seed_tasks(db: AsyncSession, cases: dict, users: dict) -> None:
    count = 0
    tasks_to_close = []
    for task_no, case_no, title, t_type, priority, status, assignee in TASK_DATA:
        case = cases.get(case_no)
        if not case:
            continue

        # Insert closed tasks as 'open' first (DB trigger requires review before close)
        insert_status = "open" if status == "closed" else status
        # Some tasks are overdue — SLA due date in the past
        is_overdue = task_no in ("TASK-2026-005", "TASK-2026-007", "TASK-2026-009", "TASK-2026-010")
        if is_overdue:
            sla = NOW - timedelta(days=5)
            completion = NOW - timedelta(days=2)
        elif priority == "P0":
            sla = NOW + timedelta(days=3)
            completion = NOW + timedelta(days=7)
        else:
            sla = NOW + timedelta(days=7)
            completion = NOW + timedelta(days=14)

        task = CorrectiveTask(
            case_id=case.id, task_no=task_no, title=title,
            description=f"Nhiệm vụ khắc phục: {title}. Yêu cầu hoàn thành theo SLA.",
            task_type=t_type, priority=priority, status=insert_status,
            sla_due_at=sla,
            completion_due_at=completion,
            completion_criteria="Hoàn thành và có bằng chứng xác nhận",
            evidence_requirement="Ảnh chụp hiện trường trước/sau xử lý",
            created_by_user_id=users["expert"].id,
        )
        db.add(task)
        await db.flush()

        db.add(TaskAssignee(
            task_id=task.id, user_id=users[assignee].id,
            responsibility_type="owner",
            accepted_at=NOW - timedelta(days=2) if status != "open" else None,
        ))

        if status == "pending_review":
            db.add(TaskReview(
                task_id=task.id, reviewer_user_id=users["expert"].id,
                review_result="needs_rework", review_note="Đang xem xét bằng chứng đã nộp",
            ))
        if status == "closed":
            # Add review first, then mark for closing
            db.add(TaskReview(
                task_id=task.id, reviewer_user_id=users["expert"].id,
                review_result="approved", review_note="Đã xác nhận hoàn thành, bằng chứng đạt yêu cầu",
            ))
            db.add(TaskComment(
                task_id=task.id, author_user_id=users["farm_mgr"].id,
                comment_text="Đã lắp đặt xong barrier tự động, gửi ảnh bằng chứng",
                comment_type="update",
            ))
            tasks_to_close.append(task)
        if status == "in_progress":
            db.add(TaskComment(
                task_id=task.id, author_user_id=users[assignee].id,
                comment_text="Đã bắt đầu triển khai, dự kiến hoàn thành trong 3 ngày",
                comment_type="update",
            ))
        count += 1
    await db.flush()

    # Now close tasks that need it (review already exists)
    for task in tasks_to_close:
        task.status = "closed"
        task.closed_by_user_id = users["expert"].id
        task.closed_at = NOW - timedelta(days=1)
    await db.flush()
    print(f"  Created {count} corrective tasks with assignees, reviews, comments")


# ═══════════════════════════════════════════════════════════════
# 9. Floorplans
# ═══════════════════════════════════════════════════════════════

FLOORPLAN_DATA = [
    ("FARM-N01", "Mặt bằng Hà Nam 1 — Khai trương 2024", date(2024, 1, 15)),
    ("FARM-N02", "Mặt bằng Bắc Ninh 1 — Khai trương 2024", date(2024, 1, 15)),
    ("FARM-N03", "Mặt bằng Thái Bình 1 — Khai trương 2024", date(2024, 1, 15)),
    ("FARM-C01", "Mặt bằng Thanh Hóa 1 — Khai trương 2024", date(2024, 1, 15)),
    ("FARM-S01", "Mặt bằng Đồng Nai 1 — Khai trương 2024", date(2024, 1, 15)),
    ("FARM-S03", "Mặt bằng Long An 1 — Khai trương 2024", date(2024, 1, 15)),
]

MARKER_TEMPLATES = [
    # (marker_type, label, x_percent, y_percent, area_suffix_to_link)
    ("gate", "Cổng chính", 5.0, 50.0, "GATE"),
    ("disinfection", "Nhà tắm sát trùng", 15.0, 50.0, "SHOWER"),
    ("feed_storage", "Kho cám", 30.0, 20.0, "FEED_STORE"),
    ("quarantine", "Khu cách ly", 80.0, 15.0, "QUARANTINE"),
    ("dead_pig_zone", "Khu xử lý heo chết", 90.0, 80.0, "DEAD_PIG"),
    ("checkpoint", "Khu đệm", 40.0, 50.0, "BUFFER"),
    ("checkpoint", "Khu sạch", 65.0, 50.0, "CLEAN"),
    ("checkpoint", "Khu bẩn", 20.0, 80.0, "DIRTY"),
    ("checkpoint", "Văn phòng", 10.0, 20.0, "OFFICE"),
]


async def _seed_floorplans(db: AsyncSession, farms: dict, areas: dict, users: dict) -> dict:
    floorplans = {}
    for farm_code, title, eff_from in FLOORPLAN_DATA:
        farm = farms.get(farm_code)
        if not farm:
            continue
        fp = FloorplanVersion(
            farm_id=farm.id, version_no=1, title=title,
            effective_from=eff_from, status="active",
            approved_by=users["region_mgr"].id, approved_at=NOW - timedelta(days=60),
        )
        db.add(fp)
        floorplans[farm_code] = fp
    await db.flush()

    marker_count = 0
    for farm_code, fp in floorplans.items():
        for m_type, m_label, x, y, area_suffix in MARKER_TEMPLATES:
            area = areas.get((farm_code, area_suffix))
            db.add(FloorplanMarker(
                floorplan_version_id=fp.id,
                area_id=area.id if area else None,
                marker_type=m_type, label=m_label,
                x_percent=x, y_percent=y,
            ))
            marker_count += 1
    await db.flush()
    print(f"  Created {len(floorplans)} floorplans with {marker_count} markers")
    return floorplans


# ═══════════════════════════════════════════════════════════════
# 10. Scar Records
# ═══════════════════════════════════════════════════════════════

SCAR_DATA = [
    # (farm_code, area_suffix, scar_type, title, description, confidence, event_date_offset_days, x, y)
    ("FARM-N03", "CLEAN", "outbreak", "Ổ dịch khu sạch Q1/2025",
     "Phát hiện ổ dịch PED tại khu sạch, nguồn lây nghi từ thức ăn nhiễm", "confirmed", 90, 45.0, 30.0),
    ("FARM-N03", "DIRTY", "repeated_breach", "Vi phạm lặp lại cổng vào",
     "Xe tải vào trại liên tục không qua sát trùng đúng quy trình, 4 lần trong 2 tháng", "confirmed", 60, 5.0, 50.0),
    ("FARM-S03", "DIRTY", "hotspot", "Hotspot thu nhận heo ngoài",
     "Khu vực nhận heo từ bên ngoài có tỷ lệ dương tính cao với PRRS", "probable", 45, 10.0, 70.0),
    ("FARM-S03", "BUFFER", "near_miss", "Suýt lây nhiễm khu đệm",
     "Phát hiện kịp thời nhân viên mang thức ăn ngoài vào khu đệm", "suspected", 30, 40.0, 55.0),
    ("FARM-C01", "BUFFER", "structural_flaw", "Lỗ hổng hàng rào khu đệm",
     "Hàng rào khu đệm bị hư hỏng, tạo lối đi tắt vào khu sạch", "confirmed", 20, 55.0, 35.0),
    ("FARM-N01", "DIRTY", "repeated_breach", "Khách không đăng ký lặp lại",
     "Người lạ xâm nhập khu vực trại 3 lần trong 1 tháng", "probable", 15, 8.0, 48.0),
]


async def _seed_scars(db: AsyncSession, farms: dict, areas: dict, floorplans: dict, cases: dict, users: dict) -> None:
    count = 0
    scars = []
    for farm_code, area_suffix, s_type, title, desc, confidence, days_ago, x, y in SCAR_DATA:
        farm = farms.get(farm_code)
        area = areas.get((farm_code, area_suffix))
        fp = floorplans.get(farm_code)
        if not farm:
            continue

        # Recurrence detection
        existing = [s for s in scars if s.farm_id == farm.id
                    and (area and s.area_id == area.id) and s.scar_type == s_type]
        rec_count = len(existing)

        scar = ScarRecord(
            farm_id=farm.id,
            floorplan_version_id=fp.id if fp else None,
            area_id=area.id if area else None,
            scar_type=s_type, title=title, description=desc,
            source_of_risk="Phân tích từ RCA và killer events",
            confidence_level=confidence,
            event_date=date.today() - timedelta(days=days_ago),
            x_percent=x, y_percent=y,
            recurrence_flag=rec_count > 0,
            recurrence_count=rec_count,
            created_by_user_id=users["expert"].id,
            validated_by_user_id=users["expert"].id if confidence == "confirmed" else None,
            validated_at=NOW - timedelta(days=days_ago - 2) if confidence == "confirmed" else None,
        )
        db.add(scar)
        scars.append(scar)
        count += 1
    await db.flush()

    # Link scars to cases
    case_scar_map = {
        "RC-2026-001": 0,  # FARM-N03 outbreak → scar[0]
        "RC-2026-002": 2,  # FARM-S03 red line → scar[2]
        "RC-2026-003": 4,  # FARM-C01 heo chết → scar[4]
        "RC-2026-004": 5,  # FARM-N01 người lạ → scar[5]
    }
    for case_no, scar_idx in case_scar_map.items():
        case = cases.get(case_no)
        if case and scar_idx < len(scars):
            db.add(ScarLink(
                scar_id=scars[scar_idx].id,
                linked_object_type="case",
                linked_object_id=case.id,
                link_reason="Case xử lý sự cố liên quan",
            ))
    await db.flush()
    print(f"  Created {count} scar records with links")


# ═══════════════════════════════════════════════════════════════
# Step 11: Lesson Learned + References + Tags
# ═══════════════════════════════════════════════════════════════

LESSON_DATA = [
    {
        "lesson_no": "LL-2026-0001",
        "title": "Quy trình sát trùng cổng chính giảm 90% nguy cơ lây nhiễm",
        "problem_context": "Trại FARM-N03 phát hiện ổ dịch lan từ cổng chính do xe vận chuyển không qua sát trùng.",
        "root_cause_summary": "Thiếu hố sát trùng tại cổng, xe ra vào không được kiểm soát.",
        "action_summary": "Lắp hố sát trùng bắt buộc, gắn camera giám sát, huấn luyện bảo vệ.",
        "outcome_summary": "Sau 3 tháng không ghi nhận lây nhiễm qua cổng chính.",
        "recurrence_observed": False,
        "applicability_scope": "Tất cả trại có cổng xe vận chuyển",
        "confidence_level": "confirmed",
        "status": "validated",
        "tags": [("farm_type", "sow"), ("issue_type", "vehicle_hygiene"), ("other", "gate")],
    },
    {
        "lesson_no": "LL-2026-0002",
        "title": "Giám sát đường đi nội bộ ngăn ngừa lây chéo giữa khu vực",
        "problem_context": "Trại FARM-S03 phát hiện vi phạm lặp lại: nhân viên đi tắt qua khu cách ly.",
        "root_cause_summary": "Bản đồ đường đi không rõ ràng, thiếu biển cấm, hàng rào khu cách ly thấp.",
        "action_summary": "Vẽ lại sơ đồ đường đi, nâng hàng rào, lắp cảm biến chuyển động tại lối tắt.",
        "outcome_summary": "Vi phạm giảm 85% sau 2 tháng triển khai.",
        "recurrence_observed": False,
        "applicability_scope": "Trại có khu cách ly tiếp giáp khu nuôi",
        "confidence_level": "confirmed",
        "status": "validated",
        "tags": [("farm_type", "finisher"), ("issue_type", "route_violation"), ("route_type", "internal_path")],
    },
    {
        "lesson_no": "LL-2026-0003",
        "title": "Xử lý heo chết tại chỗ vs vận chuyển ra ngoài",
        "problem_context": "Trại FARM-C01 xử lý xác heo chết bằng cách vận chuyển bằng xe ra bãi rác bên ngoài, gây rủi ro lây lan.",
        "root_cause_summary": "Chưa có phương án xử lý xác tại chỗ, thiếu hố ủ compost.",
        "action_summary": "Xây hố ủ compost, mua máy tiêu hủy, quy trình xử lý tại chỗ.",
        "outcome_summary": "Đang triển khai, chưa đủ dữ liệu đánh giá hiệu quả.",
        "recurrence_observed": True,
        "applicability_scope": "Trại chăn nuôi quy mô vừa trở lên",
        "confidence_level": "probable",
        "status": "draft",
        "tags": [("farm_type", "farrow_to_finish"), ("issue_type", "dead_animal_disposal"), ("season", "rainy")],
    },
]


async def _seed_lessons(db: AsyncSession, cases: dict, users: dict) -> None:
    """Seed lesson learned + references + tags."""
    # Check existence
    existing = await db.execute(
        select(LessonLearned).where(LessonLearned.lesson_no == "LL-2026-0001")
    )
    if existing.scalar_one_or_none():
        print("  Lessons already exist, skipping.")
        return

    expert = users.get("expert")
    count = 0
    for ld in LESSON_DATA:
        # Insert as draft first (DB trigger requires reference before validated)
        lesson = LessonLearned(
            lesson_no=ld["lesson_no"],
            title=ld["title"],
            problem_context=ld["problem_context"],
            root_cause_summary=ld["root_cause_summary"],
            action_summary=ld["action_summary"],
            outcome_summary=ld["outcome_summary"],
            recurrence_observed=ld["recurrence_observed"],
            applicability_scope=ld["applicability_scope"],
            confidence_level=ld["confidence_level"],
            status="draft",
        )
        db.add(lesson)
        await db.flush()

        # Add tags
        for tag_type, tag_value in ld["tags"]:
            db.add(SimilarityTag(
                lesson_id=lesson.id,
                tag_type=tag_type,
                tag_value=tag_value,
            ))

        # Link lessons to cases
        case_map = {
            "LL-2026-0001": "RC-2026-001",
            "LL-2026-0002": "RC-2026-002",
            "LL-2026-0003": "RC-2026-003",
        }
        case_no = case_map.get(ld["lesson_no"])
        if case_no and case_no in cases:
            db.add(LessonReference(
                lesson_id=lesson.id,
                reference_type="case",
                reference_id=cases[case_no].id,
                contribution_note=f"Bài học rút ra từ case {case_no}",
            ))
        await db.flush()

        # Now set status to validated if needed
        if ld["status"] == "validated":
            lesson.status = "validated"
            lesson.confirmed_by_user_id = expert.id if expert else None
            lesson.confirmed_at = NOW - timedelta(days=10)
            await db.flush()

        count += 1
    await db.flush()
    print(f"  Created {count} lesson learned with references and tags")


# ═══════════════════════════════════════════════════════════════
# Main orchestrator
# ═══════════════════════════════════════════════════════════════

async def seed_all() -> None:
    """Run all seed functions in order."""
    async with async_session_factory() as db:
        print("\n[1/11] Seeding users...")
        users = await seed_users(db)

        print("\n[2/11] Seeding regions & farms...")
        _regions, farms, areas = await _seed_regions_and_farms(db, users)

        print("\n[3/11] Seeding scorecard templates...")
        templates = await _seed_scorecards(db)

        print("\n[4/11] Seeding assessments...")
        assessments = await _seed_assessments(db, farms, templates, users)

        print("\n[5/11] Seeding trust scores...")
        await _seed_trust_scores(db, farms, assessments)

        print("\n[6/11] Seeding killer metric events...")
        await _seed_killer_events(db, farms, areas, users)

        print("\n[7/11] Seeding risk cases & RCA...")
        cases = await _seed_cases(db, farms, users)

        print("\n[8/11] Seeding corrective tasks...")
        await _seed_tasks(db, cases, users)

        print("\n[9/11] Seeding floorplans & markers...")
        floorplans = await _seed_floorplans(db, farms, areas, users)

        print("\n[10/11] Seeding scar records & links...")
        await _seed_scars(db, farms, areas, floorplans, cases, users)

        print("\n[11/11] Seeding lesson learned...")
        await _seed_lessons(db, cases, users)

        await db.commit()
        print("\n✓ All sample data seeded successfully!")


async def main():
    await seed_all()


if __name__ == "__main__":
    asyncio.run(main())
