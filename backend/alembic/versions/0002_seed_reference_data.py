"""Seed reference data from V002

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:01.000000
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def _split_sql(sql: str) -> list[str]:
    """Split SQL into individual statements, respecting $$ dollar-quoted blocks."""
    filtered_lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        filtered_lines.append(line)

    statements = []
    current = []
    in_dollar_quote = False

    for line in filtered_lines:
        current.append(line)
        stripped = line.strip()

        if not in_dollar_quote:
            if "$$" in stripped and stripped.count("$$") == 1:
                in_dollar_quote = True
                continue
            if stripped.endswith(";"):
                stmt = "\n".join(current).strip()
                if stmt.endswith(";"):
                    stmt = stmt[:-1].strip()
                if stmt:
                    statements.append(stmt)
                current = []
        else:
            if "$$" in stripped:
                in_dollar_quote = False
                if stripped.endswith(";"):
                    stmt = "\n".join(current).strip()
                    if stmt.endswith(";"):
                        stmt = stmt[:-1].strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
    return statements


def upgrade() -> None:
    sql = (SQL_DIR / "V002__seed_reference_data.sql").read_text(encoding="utf-8")
    for stmt in _split_sql(sql):
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DELETE FROM biosec.role_permission")
    op.execute("DELETE FROM biosec.app_permission")
    op.execute("DELETE FROM biosec.app_role")
    op.execute("DELETE FROM biosec.lookup_code")
    op.execute("DELETE FROM biosec.killer_metric_definition")
