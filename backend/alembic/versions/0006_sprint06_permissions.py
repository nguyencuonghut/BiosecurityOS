"""Add permissions for Sprint 06 — Corrective Task & Evidence/Attachment.

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('TASK_READ', 'Xem task khắc phục', 'task', 'read'),
    ('ATTACHMENT_UPLOAD', 'Upload bằng chứng', 'attachment', 'upload'),
    ('ATTACHMENT_READ', 'Xem bằng chứng', 'attachment', 'read'),
    ('ATTACHMENT_DELETE', 'Xóa bằng chứng', 'attachment', 'delete')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'TASK_READ'),
        ('SYSTEM_ADMIN', 'ATTACHMENT_UPLOAD'),
        ('SYSTEM_ADMIN', 'ATTACHMENT_READ'),
        ('SYSTEM_ADMIN', 'ATTACHMENT_DELETE'),

        ('REGION_MANAGER', 'TASK_READ'),
        ('REGION_MANAGER', 'ATTACHMENT_READ'),

        ('FARM_MANAGER', 'TASK_READ'),
        ('FARM_MANAGER', 'ATTACHMENT_UPLOAD'),
        ('FARM_MANAGER', 'ATTACHMENT_READ'),

        ('BIOSEC_EXPERT', 'TASK_READ'),
        ('BIOSEC_EXPERT', 'ATTACHMENT_UPLOAD'),
        ('BIOSEC_EXPERT', 'ATTACHMENT_READ'),
        ('BIOSEC_EXPERT', 'ATTACHMENT_DELETE'),

        ('AUDITOR', 'TASK_READ'),
        ('AUDITOR', 'ATTACHMENT_READ'),

        ('VIEWER', 'TASK_READ'),
        ('VIEWER', 'ATTACHMENT_READ')
)
INSERT INTO biosec.role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role_perm rp
JOIN biosec.app_role r ON r.code = rp.role_code
JOIN biosec.app_permission p ON p.code = rp.perm_code
ON CONFLICT DO NOTHING
"""

PERM_CODES = "('TASK_READ','ATTACHMENT_UPLOAD','ATTACHMENT_READ','ATTACHMENT_DELETE')"


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
