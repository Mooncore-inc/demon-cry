"""rename module to plugin

Revision ID: f3a1c9e2b847
Revises: dbbc1fe7c7c2
Create Date: 2026-09-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1c9e2b847"
down_revision: str | None = "dbbc1fe7c7c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("module"):
        op.rename_table("module", "plugin")
        inspector = sa.inspect(bind)
    if inspector.has_table("plugin"):
        columns = {c["name"] for c in inspector.get_columns("plugin")}
        if "module_name" in columns and "plugin_name" not in columns:
            op.alter_column(
                "plugin",
                "module_name",
                new_column_name="plugin_name",
                existing_type=sa.String(64),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("plugin"):
        columns = {c["name"] for c in inspector.get_columns("plugin")}
        if "plugin_name" in columns and "module_name" not in columns:
            op.alter_column(
                "plugin",
                "plugin_name",
                new_column_name="module_name",
                existing_type=sa.String(64),
            )
        op.rename_table("plugin", "module")
