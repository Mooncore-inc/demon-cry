from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from demon_cry.database.models.base import BaseModel


class LLMModel(BaseModel):
    __tablename__ = "llm_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    base_url: Mapped[str] = mapped_column(String())
    api_key: Mapped[str] = mapped_column(String())
    model_name: Mapped[str] = mapped_column(String(64), unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
