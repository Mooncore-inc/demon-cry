from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import ModuleModel
from demon_cry.database.repositories.base import BaseRepository


class ModuleRepository(BaseRepository[ModuleModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ModuleModel)
