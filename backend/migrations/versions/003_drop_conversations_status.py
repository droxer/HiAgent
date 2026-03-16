"""Drop status column from conversations table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_conversations_status", "conversations", type_="check")
    op.drop_column("conversations", "status")


def downgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
    )
    op.create_check_constraint(
        "ck_conversations_status",
        "conversations",
        "status IN ('running', 'completed', 'failed')",
    )
