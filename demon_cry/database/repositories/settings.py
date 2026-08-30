from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models.settings import Settings
from demon_cry.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Settings)
