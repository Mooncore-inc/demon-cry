from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.repositories import (
    LLMRepository,
    PluginRepository,
    SettingsRepository,
    UserRepository,
)
from demon_cry.database.uow_base import UnitOfWorkBase


class AppUnitOfWork(UnitOfWorkBase):
    """App-обвязка"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.users = UserRepository(session)
        self.settings = SettingsRepository(session)
        self.plugins = PluginRepository(session)
        self.llms = LLMRepository(session)
