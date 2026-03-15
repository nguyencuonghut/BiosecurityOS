"""Initial schema from V001

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
import re
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def _split_sql(sql: str) -> list[str]:
    """Split SQL into individual statements, respecting $$ dollar-quoted blocks."""
    # Strip standalone comment lines (-- ...) before parsing
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
    sql = (SQL_DIR / "V001__init_schema.sql").read_text(encoding="utf-8")
    for stmt in _split_sql(sql):
        op.execute(stmt)


def downgrade() -> None:
    sql = (SQL_DIR / "V001__init_schema_down.sql").read_text(encoding="utf-8")
    for stmt in _split_sql(sql):
        op.execute(stmt)
