"""Add permissions for Sprint 08 — Lesson Learned.

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('LESSON_READ', 'Xem lesson learned', 'lesson', 'read'),
    ('LESSON_WRITE', 'Tạo/cập nhật lesson learned', 'lesson', 'update')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'LESSON_READ'),
        ('SYSTEM_ADMIN', 'LESSON_WRITE'),

        ('REGION_MANAGER', 'LESSON_READ'),

        ('FARM_MANAGER', 'LESSON_READ'),

        ('BIOSEC_EXPERT', 'LESSON_READ'),
        ('BIOSEC_EXPERT', 'LESSON_WRITE'),

        ('AUDITOR', 'LESSON_READ'),

        ('VIEWER', 'LESSON_READ')
)
INSERT INTO biosec.role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role_perm rp
JOIN biosec.app_role r ON r.code = rp.role_code
JOIN biosec.app_permission p ON p.code = rp.perm_code
ON CONFLICT DO NOTHING
"""

PERM_CODES = "('LESSON_READ','LESSON_WRITE')"


def upgrade() -> None:
    op.execute(PERMISSIONS_SQL)
    op.execute(ROLE_PERMS_SQL)


def downgrade() -> None:
    op.execute(f"""
        DELETE FROM biosec.role_permission
        WHERE permission_id IN (
            SELECT id FROM biosec.app_permission
            WHERE code IN {PERM_CODES}
        )
    """)
    op.execute(f"""
        DELETE FROM biosec.app_permission
        WHERE code IN {PERM_CODES}
    """)
