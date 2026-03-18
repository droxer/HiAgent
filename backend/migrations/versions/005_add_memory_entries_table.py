"""Add memory_entries table for persistent agent memory.

Revision ID: 005
Revises: 004
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    if "memory_entries" in inspector.get_table_names():
        return

    op.create_table(
        "memory_entries",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "namespace", sa.String(255), nullable=False, server_default="default"
        ),
        sa.Column("key", sa.String(500), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_memory_ns_key", "memory_entries", ["namespace", "key"])
    op.create_index("ix_memory_conversation", "memory_entries", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_conversation", table_name="memory_entries")
    op.drop_index("ix_memory_ns_key", table_name="memory_entries")
    op.drop_table("memory_entries")
