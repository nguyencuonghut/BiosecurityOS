"""Add DASHBOARD_VIEW permission for Sprint 09.

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('DASHBOARD_VIEW', 'Xem dashboard & analytics', 'dashboard', 'read')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN',   'DASHBOARD_VIEW'),
        ('REGION_MANAGER', 'DASHBOARD_VIEW'),
        ('FARM_MANAGER',   'DASHBOARD_VIEW'),
        ('BIOSEC_EXPERT',  'DASHBOARD_VIEW'),
        ('AUDITOR',        'DASHBOARD_VIEW'),
        ('VIEWER',         'DASHBOARD_VIEW')
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
            SELECT id FROM biosec.app_permission WHERE code = 'DASHBOARD_VIEW'
        )
    """)
    op.execute("DELETE FROM biosec.app_permission WHERE code = 'DASHBOARD_VIEW'")
