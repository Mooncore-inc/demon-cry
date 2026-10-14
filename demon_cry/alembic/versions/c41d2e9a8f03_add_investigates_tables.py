"""add investigates tables

Revision ID: c41d2e9a8f03
Revises: f3a1c9e2b847
Create Date: 2026-10-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c41d2e9a8f03"
down_revision: str | None = "f3a1c9e2b847"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigates_owner_id", "investigates", ["owner_id"])

    op.create_table(
        "investigates_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigate_id", sa.Integer(), nullable=False),
        sa.Column("plugin_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("entities", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigates_data_investigate_id", "investigates_data", ["investigate_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_investigates_data_investigate_id", table_name="investigates_data")
    op.drop_table("investigates_data")
    op.drop_index("ix_investigates_owner_id", table_name="investigates")
    op.drop_table("investigates")
