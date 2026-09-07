from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import LLMModel
from demon_cry.database.repositories.base import BaseRepository


class LLMRepository(BaseRepository[LLMModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, LLMModel)
