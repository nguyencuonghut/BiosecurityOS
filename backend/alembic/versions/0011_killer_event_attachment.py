"""Add killer_event_attachment junction table for evidence on killer metric events.

FR-08a: Mỗi sự kiện killer metric phải hỗ trợ đính kèm bằng chứng (ảnh/video).
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biosec.killer_event_attachment (
            id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
            event_id uuid NOT NULL,
            attachment_id uuid NOT NULL,
            caption text
        )
    """)

    # Foreign keys
    op.execute(
        "ALTER TABLE biosec.killer_event_attachment "
        "ADD CONSTRAINT fk_killer_event_attachment_event_id "
        "FOREIGN KEY (event_id) REFERENCES biosec.killer_metric_event(id) ON DELETE CASCADE"
    )
    op.execute(
        "ALTER TABLE biosec.killer_event_attachment "
        "ADD CONSTRAINT fk_killer_event_attachment_attachment_id "
        "FOREIGN KEY (attachment_id) REFERENCES biosec.attachment(id) ON DELETE CASCADE"
    )

    # Unique constraint
    op.execute(
        "ALTER TABLE biosec.killer_event_attachment "
        "ADD CONSTRAINT uq_killer_event_attachment_event_id_attachment_id "
        "UNIQUE (event_id, attachment_id)"
    )

    # Indexes
    op.execute(
        "CREATE INDEX idx_killer_event_attachment_event_id "
        "ON biosec.killer_event_attachment (event_id)"
    )
    op.execute(
        "CREATE INDEX idx_killer_event_attachment_attachment_id "
        "ON biosec.killer_event_attachment (attachment_id)"
    )

    # Comments
    op.execute("COMMENT ON TABLE biosec.killer_event_attachment IS $$ Bảng file bằng chứng gắn cho sự kiện killer metric. $$")
    op.execute("COMMENT ON COLUMN biosec.killer_event_attachment.id IS $$ Khóa chính (PK) của bảng. $$")
    op.execute("COMMENT ON COLUMN biosec.killer_event_attachment.event_id IS $$ Sự kiện killer metric mà file bằng chứng đính kèm. $$")
    op.execute("COMMENT ON COLUMN biosec.killer_event_attachment.attachment_id IS $$ File bằng chứng thực tế (ảnh/video). $$")
    op.execute("COMMENT ON COLUMN biosec.killer_event_attachment.caption IS $$ Chú thích ngắn cho file. $$")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS biosec.killer_event_attachment")
