from sqlalchemy import String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


class ModuleModel(BaseModel):
    __tablename__ = "module"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    module_name: Mapped[str] = mapped_column(String(64), unique=True)
    config: Mapped[dict] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
