"""Add permissions for Sprint 04 — Trust Score & Killer Metrics.

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-16 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('TRUST_SCORE_READ', 'Xem trust score', 'trust_score', 'read'),
    ('TRUST_SCORE_WRITE', 'Tính trust score', 'trust_score', 'update'),
    ('KILLER_EVENT_READ', 'Xem killer metric event', 'killer_metric', 'read'),
    ('KILLER_EVENT_WRITE', 'Tạo/sửa killer metric event', 'killer_metric', 'update')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'TRUST_SCORE_READ'),
        ('SYSTEM_ADMIN', 'TRUST_SCORE_WRITE'),
        ('SYSTEM_ADMIN', 'KILLER_EVENT_READ'),
        ('SYSTEM_ADMIN', 'KILLER_EVENT_WRITE'),

        ('REGION_MANAGER', 'TRUST_SCORE_READ'),
        ('REGION_MANAGER', 'KILLER_EVENT_READ'),

        ('FARM_MANAGER', 'TRUST_SCORE_READ'),
        ('FARM_MANAGER', 'KILLER_EVENT_READ'),
        ('FARM_MANAGER', 'KILLER_EVENT_WRITE'),

        ('BIOSEC_EXPERT', 'TRUST_SCORE_READ'),
        ('BIOSEC_EXPERT', 'TRUST_SCORE_WRITE'),
        ('BIOSEC_EXPERT', 'KILLER_EVENT_READ'),
        ('BIOSEC_EXPERT', 'KILLER_EVENT_WRITE'),

        ('AUDITOR', 'TRUST_SCORE_READ'),
        ('AUDITOR', 'KILLER_EVENT_READ'),
        ('AUDITOR', 'KILLER_EVENT_WRITE'),

        ('VIEWER', 'TRUST_SCORE_READ'),
        ('VIEWER', 'KILLER_EVENT_READ')
)
INSERT INTO biosec.role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role_perm rp
JOIN biosec.app_role r ON r.code = rp.role_code
JOIN biosec.app_permission p ON p.code = rp.perm_code
ON CONFLICT DO NOTHING
"""


def upgrade() -> None:
    op.execute(PERMISSIONS_SQL)
    op.execute(ROLE_PERMS_SQL)


def downgrade() -> None:
    op.execute("""
        DELETE FROM biosec.role_permission
        WHERE permission_id IN (
            SELECT id FROM biosec.app_permission
            WHERE code IN ('TRUST_SCORE_READ','TRUST_SCORE_WRITE','KILLER_EVENT_READ','KILLER_EVENT_WRITE')
        )
    """)
    op.execute("""
        DELETE FROM biosec.app_permission
        WHERE code IN ('TRUST_SCORE_READ','TRUST_SCORE_WRITE','KILLER_EVENT_READ','KILLER_EVENT_WRITE')
    """)
