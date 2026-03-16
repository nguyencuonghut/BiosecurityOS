"""Add SCORECARD and ASSESSMENT permissions for Sprint 03.

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:00:02.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('SCORECARD_READ', 'Xem template scorecard', 'scorecard', 'read'),
    ('SCORECARD_WRITE', 'Tạo/sửa template scorecard', 'scorecard', 'update'),
    ('ASSESSMENT_READ', 'Xem phiếu đánh giá', 'assessment', 'read'),
    ('ASSESSMENT_WRITE', 'Tạo/sửa phiếu đánh giá', 'assessment', 'update')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'SCORECARD_READ'),
        ('SYSTEM_ADMIN', 'SCORECARD_WRITE'),
        ('SYSTEM_ADMIN', 'ASSESSMENT_READ'),
        ('SYSTEM_ADMIN', 'ASSESSMENT_WRITE'),

        ('REGION_MANAGER', 'SCORECARD_READ'),
        ('REGION_MANAGER', 'ASSESSMENT_READ'),

        ('FARM_MANAGER', 'SCORECARD_READ'),
        ('FARM_MANAGER', 'ASSESSMENT_READ'),
        ('FARM_MANAGER', 'ASSESSMENT_WRITE'),

        ('BIOSEC_EXPERT', 'SCORECARD_READ'),
        ('BIOSEC_EXPERT', 'SCORECARD_WRITE'),
        ('BIOSEC_EXPERT', 'ASSESSMENT_READ'),
        ('BIOSEC_EXPERT', 'ASSESSMENT_WRITE'),

        ('AUDITOR', 'SCORECARD_READ'),
        ('AUDITOR', 'ASSESSMENT_READ'),
        ('AUDITOR', 'ASSESSMENT_WRITE'),

        ('VIEWER', 'SCORECARD_READ'),
        ('VIEWER', 'ASSESSMENT_READ')
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
            WHERE code IN ('SCORECARD_READ','SCORECARD_WRITE','ASSESSMENT_READ','ASSESSMENT_WRITE')
        )
    """)
    op.execute("""
        DELETE FROM biosec.app_permission
        WHERE code IN ('SCORECARD_READ','SCORECARD_WRITE','ASSESSMENT_READ','ASSESSMENT_WRITE')
    """)
