from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InvestigatesModel(BaseModel):
    __tablename__ = "investigates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


class InvestigatesDataModel(BaseModel):
    __tablename__ = "investigates_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    investigate_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    plugin_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    entities: Mapped[dict] = mapped_column(JSON)
    errors: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
