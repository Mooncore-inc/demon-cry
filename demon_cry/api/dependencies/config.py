from typing import Annotated
from fastapi import Depends

from demon_cry.config import Config
from demon_cry.llm import LLM
from demon_cry.module_registry import registry


async def get_config() -> Config:
    return await Config.load()

AppConfig = Annotated[Config, Depends(get_config)]


def get_llm(config: Config = Depends(get_config)) -> LLM:
    return LLM(config=config, registry=registry, system_prompt=config.system_prompt)

AppLLM = Annotated[LLM, Depends(get_llm)]
