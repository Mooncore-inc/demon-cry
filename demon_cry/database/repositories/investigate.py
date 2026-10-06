from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import InvestigatesModel
from demon_cry.database.repositories.base import BaseRepository


class InvestigatesRepository(BaseRepository[InvestigatesModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InvestigatesModel)
