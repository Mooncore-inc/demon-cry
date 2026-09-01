from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


class SettingsModel(BaseModel):
    __tablename__ = "kv_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(Text)
