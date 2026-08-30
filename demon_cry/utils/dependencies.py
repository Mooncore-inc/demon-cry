from fastapi import Depends

from demon_cry.config import Config
from demon_cry.llm import LLM
from demon_cry.module_registry import registry

from demon_cry.database.engine import get_session
from demon_cry.database.repositories.settings import SettingsRepository


async def get_config() -> Config:
    return await Config.load()


def get_llm(
        config: Config = Depends(get_config)
        ) -> LLM:
    return LLM(config=config, registry=registry, system_prompt=config.system_prompt)


def get_settings_repo(session=Depends(get_session)):
    return SettingsRepository(session)
