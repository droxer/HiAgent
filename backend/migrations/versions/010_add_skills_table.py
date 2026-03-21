"""Add skills table for skill metadata and usage tracking.

Revision ID: 010
Revises: 009
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("name", sa.String(64), primary_key=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_path", sa.String(500), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("activation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "installed_at",
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
    op.create_index("ix_skills_source_type", "skills", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_skills_source_type", table_name="skills")
    op.drop_table("skills")
