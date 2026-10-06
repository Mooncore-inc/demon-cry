from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


class InvestigatesModel(BaseModel):
    __tablename__ = "investigates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
