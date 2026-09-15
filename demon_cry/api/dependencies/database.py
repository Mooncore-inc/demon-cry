from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.engine import get_session
from demon_cry.database.repositories import (
    LLMRepository,
    PluginRepository,
    SettingsRepository,
    UserRepository,
)

Session = Annotated[AsyncSession, Depends(get_session)]


def get_settings_repo(session: Session) -> SettingsRepository:
    return SettingsRepository(session)


SettingsRepo = Annotated[SettingsRepository, Depends(get_settings_repo)]


def get_plugin_repo(session: Session) -> PluginRepository:
    return PluginRepository(session)


PluginRepo = Annotated[PluginRepository, Depends(get_plugin_repo)]


def get_user_repo(session: Session) -> UserRepository:
    return UserRepository(session)


UserRepo = Annotated[UserRepository, Depends(get_user_repo)]


def get_llm_repo(session: Session) -> LLMRepository:
    return LLMRepository(session)


LLMRepo = Annotated[LLMRepository, Depends(get_llm_repo)]
