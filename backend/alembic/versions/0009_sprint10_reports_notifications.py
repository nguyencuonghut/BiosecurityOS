"""Sprint 10 — Reports, Notifications & Audit Log permissions + report_request table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── report_request table ────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS biosec.report_request (
    id              uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    requested_by    uuid NOT NULL REFERENCES biosec.app_user(id) ON DELETE CASCADE,
    report_type     varchar(50) NOT NULL,
    format          varchar(10) NOT NULL DEFAULT 'xlsx',
    filters         jsonb,
    status          varchar(20) NOT NULL DEFAULT 'pending',
    file_path       text,
    error_message   text,
    completed_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_report_request_status CHECK (status IN ('pending','processing','completed','failed')),
    CONSTRAINT ck_report_request_format CHECK (format IN ('xlsx','csv','pdf'))
);

CREATE INDEX IF NOT EXISTS idx_report_request_requested_by ON biosec.report_request (requested_by);
CREATE INDEX IF NOT EXISTS idx_report_request_status ON biosec.report_request (status);
"""

DROP_TABLE_SQL = """
DROP TABLE IF EXISTS biosec.report_request;
"""

# ── Permissions ─────────────────────────────────────────────────
PERMISSIONS_SQL = """
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('NOTIFICATION_READ', 'Xem thông báo', 'notification', 'read'),
    ('AUDIT_LOG_READ', 'Xem audit log', 'audit_log', 'read'),
    ('REPORT_GENERATE', 'Tạo và tải báo cáo', 'report', 'create')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action
"""

# NOTIFICATION_READ: all roles
# AUDIT_LOG_READ: SYSTEM_ADMIN only
# REPORT_GENERATE: SYSTEM_ADMIN, REGION_MANAGER, BIOSEC_EXPERT
ROLE_PERMS_SQL = """
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN',   'NOTIFICATION_READ'),
        ('REGION_MANAGER', 'NOTIFICATION_READ'),
        ('FARM_MANAGER',   'NOTIFICATION_READ'),
        ('BIOSEC_EXPERT',  'NOTIFICATION_READ'),
        ('AUDITOR',        'NOTIFICATION_READ'),
        ('VIEWER',         'NOTIFICATION_READ'),

        ('SYSTEM_ADMIN',   'AUDIT_LOG_READ'),

        ('SYSTEM_ADMIN',   'REPORT_GENERATE'),
        ('REGION_MANAGER', 'REPORT_GENERATE'),
        ('BIOSEC_EXPERT',  'REPORT_GENERATE')
)
INSERT INTO biosec.role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role_perm rp
JOIN biosec.app_role r ON r.code = rp.role_code
JOIN biosec.app_permission p ON p.code = rp.perm_code
ON CONFLICT DO NOTHING
"""


def upgrade() -> None:
    # Create table
    op.execute("""
        CREATE TABLE IF NOT EXISTS biosec.report_request (
            id              uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
            requested_by    uuid NOT NULL REFERENCES biosec.app_user(id) ON DELETE CASCADE,
            report_type     varchar(50) NOT NULL,
            format          varchar(10) NOT NULL DEFAULT 'xlsx',
            filters         jsonb,
            status          varchar(20) NOT NULL DEFAULT 'pending',
            file_path       text,
            error_message   text,
            completed_at    timestamptz,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_report_request_status CHECK (status IN ('pending','processing','completed','failed')),
            CONSTRAINT ck_report_request_format CHECK (format IN ('xlsx','csv','pdf'))
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_report_request_requested_by ON biosec.report_request (requested_by)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_report_request_status ON biosec.report_request (status)")

    # Permissions
    op.execute(PERMISSIONS_SQL)
    op.execute(ROLE_PERMS_SQL)


def downgrade() -> None:
    op.execute("""
        DELETE FROM biosec.role_permission
        WHERE permission_id IN (
            SELECT id FROM biosec.app_permission
            WHERE code IN ('NOTIFICATION_READ', 'AUDIT_LOG_READ', 'REPORT_GENERATE')
        )
    """)
    op.execute("""
        DELETE FROM biosec.app_permission
        WHERE code IN ('NOTIFICATION_READ', 'AUDIT_LOG_READ', 'REPORT_GENERATE')
    """)
    op.execute(DROP_TABLE_SQL)
