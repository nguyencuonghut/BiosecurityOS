"""Sprint 11 — Performance indexes for top queries.

Covers dashboard subqueries, list endpoints, and common filter patterns.
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Assessment: dashboard DISTINCT ON (farm_id ORDER BY assessment_date DESC)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_assessment_farm_date_desc "
        "ON biosec.assessment (farm_id, assessment_date DESC) "
        "WHERE status != 'draft'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_assessment_status "
        "ON biosec.assessment (status)"
    )

    # ── RiskCase: open cases count, case queue filters
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_risk_case_status_priority "
        "ON biosec.risk_case (current_status, priority) "
        "WHERE archived_at IS NULL"
    )

    # ── CorrectiveTask: overdue tasks, task list filters
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_corrective_task_status_sla "
        "ON biosec.corrective_task (status, sla_due_at) "
        "WHERE archived_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_corrective_task_case "
        "ON biosec.corrective_task (case_id)"
    )

    # ── KillerMetricEvent: open events, trend queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_km_event_status "
        "ON biosec.killer_metric_event (status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_km_event_farm_detected "
        "ON biosec.killer_metric_event (farm_id, event_at DESC)"
    )

    # ── TrustScoreSnapshot: latest per farm
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trust_snapshot_farm_date "
        "ON biosec.trust_score_snapshot (farm_id, snapshot_date DESC)"
    )

    # ── ScarRecord: scar map, hotspot queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scar_record_farm "
        "ON biosec.scar_record (farm_id) "
        "WHERE archived_at IS NULL"
    )

    # ── Notification: user's unread notifications
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_notification_recipient_status "
        "ON biosec.notification (recipient_user_id, status)"
    )

    # ── AuditLog: admin log queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_log_created "
        "ON biosec.audit_log (occurred_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_log_actor "
        "ON biosec.audit_log (actor_user_id)"
    )

    # ── ReportRequest: user's report history
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_report_request_user_created "
        "ON biosec.report_request (requested_by, created_at DESC)"
    )

    # ── Farm: common filters
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_farm_region_status "
        "ON biosec.farm (region_id, operational_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS biosec.idx_assessment_farm_date_desc")
    op.execute("DROP INDEX IF EXISTS biosec.idx_assessment_status")
    op.execute("DROP INDEX IF EXISTS biosec.idx_risk_case_status_priority")
    op.execute("DROP INDEX IF EXISTS biosec.idx_corrective_task_status_sla")
    op.execute("DROP INDEX IF EXISTS biosec.idx_corrective_task_case")
    op.execute("DROP INDEX IF EXISTS biosec.idx_km_event_status")
    op.execute("DROP INDEX IF EXISTS biosec.idx_km_event_farm_detected")
    op.execute("DROP INDEX IF EXISTS biosec.idx_trust_snapshot_farm_date")
    op.execute("DROP INDEX IF EXISTS biosec.idx_scar_record_farm")
    op.execute("DROP INDEX IF EXISTS biosec.idx_notification_recipient_status")
    op.execute("DROP INDEX IF EXISTS biosec.idx_audit_log_created")
    op.execute("DROP INDEX IF EXISTS biosec.idx_audit_log_actor")
    op.execute("DROP INDEX IF EXISTS biosec.idx_report_request_user_created")
    op.execute("DROP INDEX IF EXISTS biosec.idx_farm_region_status")
