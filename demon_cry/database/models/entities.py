from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InvestigateEntityModel(BaseModel):
    """Инстанция энтити на графе исследования.

    Сознательно без дедупа: каждое появление — отдельная запись.
    """

    __tablename__ = "investigate_entities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    investigate_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    type: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(8), nullable=False)
    source_run_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


class InvestigateEntityLinkModel(BaseModel):
    """Направленная связь между двумя энтити одного исследования."""

    __tablename__ = "investigate_entity_links"
    __table_args__ = (
        # Точный дубликат связи невозможен; пары с иным relation/origin — можно.
        UniqueConstraint(
            "investigate_id",
            "source_id",
            "target_id",
            "relation",
            "origin",
            name="uq_investigate_entity_links",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    investigate_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    origin: Mapped[str] = mapped_column(String(8), nullable=False)
    source_run_id: Mapped[int | None] = mapped_column(Integer)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
