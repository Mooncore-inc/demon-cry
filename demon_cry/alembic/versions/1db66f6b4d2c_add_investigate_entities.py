"""add investigate entities tables

Revision ID: 1db66f6b4d2c
Revises: c41d2e9a8f03
Create Date: 2026-10-30

"""

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1db66f6b4d2c"
down_revision: str | None = "c41d2e9a8f03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BATCH_SIZE = 500

logger = logging.getLogger("demon_cry.alembic.entities")


def upgrade() -> None:
    op.create_table(
        "investigate_entities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigate_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=True),
        sa.Column("value", sa.String(length=1024), nullable=False),
        sa.Column("label", sa.String(length=256), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=8), nullable=False),
        sa.Column("source_run_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigate_entities_investigate_id",
        "investigate_entities",
        ["investigate_id"],
    )
    op.create_index("ix_investigate_entities_type", "investigate_entities", ["type"])
    op.create_index(
        "ix_investigate_entities_source_run_id",
        "investigate_entities",
        ["source_run_id"],
    )

    op.create_table(
        "investigate_entity_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigate_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("relation", sa.String(length=64), nullable=False),
        sa.Column("origin", sa.String(length=8), nullable=False),
        sa.Column("source_run_id", sa.Integer(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "investigate_id",
            "source_id",
            "target_id",
            "relation",
            "origin",
            name="uq_investigate_entity_links",
        ),
    )
    op.create_index(
        "ix_investigate_entity_links_investigate_id",
        "investigate_entity_links",
        ["investigate_id"],
    )
    op.create_index(
        "ix_investigate_entity_links_source_id",
        "investigate_entity_links",
        ["source_id"],
    )
    op.create_index(
        "ix_investigate_entity_links_target_id",
        "investigate_entity_links",
        ["target_id"],
    )

    _backfill()


def _backfill() -> None:
    """Каждая старая энтити из investigates_data -> своя инстанция.

    Без дедупа и без связей: родителей в старых данных нет. Ошибки per-row
    аккумулируются как warning и не прерывают миграцию.
    """
    try:
        from demon_cry.services.entities import extract_entities
    except Exception:  # pragma: no cover - защита от обращения из alembic-окружения
        logger.warning("entities extractor unavailable, backfill skipped", exc_info=True)
        return

    conn = op.get_bind()
    entities_t = sa.table(
        "investigate_entities",
        sa.column("investigate_id", sa.Integer),
        sa.column("type", sa.String),
        sa.column("value", sa.String),
        sa.column("label", sa.String),
        sa.column("data", sa.JSON),
        sa.column("source", sa.String),
        sa.column("source_run_id", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    runs_t = sa.table(
        "investigates_data",
        sa.column("id", sa.Integer),
        sa.column("investigate_id", sa.Integer),
        sa.column("entities", sa.JSON),
    )

    runs = 0
    created = 0
    failed = 0
    after = 0
    now = datetime.now(UTC)
    while True:
        rows = conn.execute(
            sa.select(runs_t.c.id, runs_t.c.investigate_id, runs_t.c.entities)
            .where(runs_t.c.id > after)
            .order_by(runs_t.c.id)
            .limit(BATCH_SIZE)
        ).mappings().all()
        if not rows:
            break
        for row in rows:
            runs += 1
            after = row["id"]
            entities_raw = row["entities"]
            try:
                if isinstance(entities_raw, str):
                    entities_raw = json.loads(entities_raw)
                drafts = extract_entities(entities_raw)
            except Exception:
                failed += 1
                logger.warning(
                    "backfill: skip investigates_data id=%s", row["id"], exc_info=True
                )
                continue
            if not drafts:
                continue
            conn.execute(
                sa.insert(entities_t),
                [
                    {
                        "investigate_id": row["investigate_id"],
                        "type": draft["type"],
                        "value": draft["value"],
                        "label": None,
                        "data": draft["data"],
                        "source": "plugin",
                        "source_run_id": row["id"],
                        "created_at": now,
                    }
                    for draft in drafts
                ],
            )
            created += len(drafts)
    logger.info(
        "backfill summary: runs=%d, entities=%d, failed=%d (raw log untouched)",
        runs,
        created,
        failed,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_investigate_entity_links_target_id", table_name="investigate_entity_links"
    )
    op.drop_index(
        "ix_investigate_entity_links_source_id", table_name="investigate_entity_links"
    )
    op.drop_index(
        "ix_investigate_entity_links_investigate_id",
        table_name="investigate_entity_links",
    )
    op.drop_table("investigate_entity_links")

    op.drop_index(
        "ix_investigate_entities_source_run_id", table_name="investigate_entities"
    )
    op.drop_index("ix_investigate_entities_type", table_name="investigate_entities")
    op.drop_index(
        "ix_investigate_entities_investigate_id", table_name="investigate_entities"
    )
    op.drop_table("investigate_entities")
