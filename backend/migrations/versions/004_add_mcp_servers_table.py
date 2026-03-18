"""Add mcp_servers table for persisting MCP server configurations.

Revision ID: 004
Revises: 003
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guard: table may already exist from create_all at startup.
    conn = op.get_bind()
    inspector = inspect(conn)
    if "mcp_servers" in inspector.get_table_names():
        return

    op.create_table(
        "mcp_servers",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("transport", sa.String(10), nullable=False),
        sa.Column("command", sa.String(500), nullable=False, server_default=""),
        sa.Column("args", sa.Text, nullable=False, server_default="[]"),
        sa.Column("url", sa.String(1000), nullable=False, server_default=""),
        sa.Column("env", sa.Text, nullable=False, server_default="{}"),
        sa.Column("timeout", sa.Float, nullable=False, server_default="30.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_mcp_servers_name", "mcp_servers", ["name"])


def downgrade() -> None:
    op.drop_index("ix_mcp_servers_name", table_name="mcp_servers")
    op.drop_table("mcp_servers")
