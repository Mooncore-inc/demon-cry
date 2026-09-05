from typing import Annotated
from fastapi import Depends

from demon_cry.database.engine import get_session

from demon_cry.database.repositories import SettingsRepository, UserRepository

def get_settings_repo(session=Depends(get_session)) -> SettingsRepository:
    return SettingsRepository(session)

SettingsRepo = Annotated[SettingsRepository, Depends(get_settings_repo)]

def get_user_repo(session=Depends(get_session)) -> UserRepository:
    return UserRepository(session)

UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
