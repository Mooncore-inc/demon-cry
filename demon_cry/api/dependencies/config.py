from typing import Annotated
from fastapi import Depends, Request

from demon_cry.core.config import Config
from demon_cry.services.llm import LLM
from demon_cry.core.module_registry import ModuleRegistry

async def get_config() -> Config:
    return await Config.load()

AppConfig = Annotated[Config, Depends(get_config)]

def get_registry(request: Request) -> ModuleRegistry:
    return request.app.state.registry

AppRegistry = Annotated[ModuleRegistry, Depends(get_registry)]

def get_llm(config: AppConfig, registry: AppRegistry) -> LLM:
    return LLM(config=config, registry=registry, system_prompt=config.system_prompt)

AppLLM = Annotated[LLM, Depends(get_llm)]
