"""Add permissions for Sprint 05 — Risk Case & RCA.

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('CASE_CREATE', 'Mở case rủi ro', 'case', 'create'),
    ('CASE_ASSIGN', 'Phân công chuyên gia cho case', 'case', 'assign'),
    ('RCA_WRITE', 'Lập RCA', 'rca', 'create')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'CASE_CREATE'),
        ('SYSTEM_ADMIN', 'CASE_ASSIGN'),
        ('SYSTEM_ADMIN', 'RCA_WRITE'),

        ('REGION_MANAGER', 'CASE_CREATE'),
        ('REGION_MANAGER', 'CASE_ASSIGN'),

        ('FARM_MANAGER', 'CASE_CREATE'),

        ('BIOSEC_EXPERT', 'CASE_CREATE'),
        ('BIOSEC_EXPERT', 'CASE_ASSIGN'),
        ('BIOSEC_EXPERT', 'RCA_WRITE'),

        ('AUDITOR', 'CASE_CREATE')
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
            WHERE code IN ('CASE_CREATE','CASE_ASSIGN','RCA_WRITE')
        )
    """)
    op.execute("""
        DELETE FROM biosec.app_permission
        WHERE code IN ('CASE_CREATE','CASE_ASSIGN','RCA_WRITE')
    """)
