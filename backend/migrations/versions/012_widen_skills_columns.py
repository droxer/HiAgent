"""Widen skills description and source_path columns.

Some skill descriptions exceed 500 chars. Increase to TEXT
for description and 1000 for source_path.

Revision ID: 012
Revises: 011
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("skills", "description", type_=sa.Text(), existing_nullable=False)
    op.alter_column(
        "skills", "source_path", type_=sa.String(1000), existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "skills", "source_path", type_=sa.String(500), existing_nullable=False
    )
    op.alter_column(
        "skills", "description", type_=sa.String(500), existing_nullable=False
    )
