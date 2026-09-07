from typing import Annotated
from fastapi import Depends

from demon_cry.database.engine import get_session

from demon_cry.database.repositories import SettingsRepository, UserRepository, ModuleRepository, LLMRepository

def get_settings_repo(session=Depends(get_session)) -> SettingsRepository:
    return SettingsRepository(session)

SettingsRepo = Annotated[SettingsRepository, Depends(get_settings_repo)]

def get_module_repo(session=Depends(get_session)) -> ModuleRepository:
    return ModuleRepository(session)

ModuleRepo = Annotated[ModuleRepository, Depends(get_module_repo)]

def get_user_repo(session=Depends(get_session)) -> UserRepository:
    return UserRepository(session)

UserRepo = Annotated[UserRepository, Depends(get_user_repo)]

def get_llm_repo(session=Depends(get_session)) -> LLMRepository:
    return LLMRepository(session)

LLMRepo = Annotated[LLMRepository, Depends(get_llm_repo)]
