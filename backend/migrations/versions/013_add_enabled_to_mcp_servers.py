"""Add enabled column to mcp_servers table.

Revision ID: 013
Revises: 012
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mcp_servers",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("mcp_servers", "enabled")
