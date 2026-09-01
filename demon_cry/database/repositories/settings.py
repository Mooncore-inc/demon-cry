from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import SettingsModel
from demon_cry.database.repositories import BaseRepository


class SettingsRepository(BaseRepository[SettingsModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SettingsModel)
