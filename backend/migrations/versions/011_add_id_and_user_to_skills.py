"""Add id (UUID PK) and user_id (nullable FK) to skills table.

Replaces the name-only primary key with a UUID id column.
Adds nullable user_id FK — NULL for bundled/shared skills,
set for user-installed skills. Unique constraint on
(user_id, name) ensures one record per user per skill.

Revision ID: 011
Revises: 010
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old primary key on name
    op.execute("ALTER TABLE skills DROP CONSTRAINT skills_pkey")

    # Add id column as new primary key
    op.add_column(
        "skills",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.create_primary_key("skills_pkey", "skills", ["id"])

    # Add nullable user_id column (NULL = bundled/shared skill)
    op.add_column(
        "skills",
        sa.Column("user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_skills_user_id",
        "skills",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add indexes
    op.create_index("ix_skills_user_id", "skills", ["user_id"])
    op.create_index("ix_skills_user_name", "skills", ["user_id", "name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_skills_user_name", table_name="skills")
    op.drop_index("ix_skills_user_id", table_name="skills")
    op.drop_constraint("fk_skills_user_id", "skills", type_="foreignkey")
    op.drop_column("skills", "user_id")

    # Restore name as primary key
    op.execute("ALTER TABLE skills DROP CONSTRAINT skills_pkey")
    op.drop_column("skills", "id")
    op.create_primary_key("skills_pkey", "skills", ["name"])
