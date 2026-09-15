from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import PluginModel
from demon_cry.database.repositories.base import BaseRepository


class PluginRepository(BaseRepository[PluginModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PluginModel)
