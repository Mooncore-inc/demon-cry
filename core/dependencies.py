from fastapi import Depends
from pathlib import Path

from core.config import Config
from core.llm import LLM
from core.module_registry import registry

def lazy_load():
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    system_prompt_template = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")
    return system_prompt_template

def get_config() -> Config:
    return Config("config.json")

def get_llm(
        config: Config = Depends(get_config)
        ) -> LLM:
    return LLM(config=config, registry=registry, system_prompt=lazy_load())
