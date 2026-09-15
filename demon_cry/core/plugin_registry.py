import logging
from importlib.metadata import entry_points
from typing import Any, TypedDict

from demon_cry_base import BaseModule

from demon_cry.database.engine import async_session_factory
from demon_cry.database.repositories import ModuleRepository


class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolDefinition(TypedDict):
    type: str
    function: ToolFunction


logger = logging.getLogger(__name__)


class ModuleRegistry:
    def __init__(self):
        self.modules: dict[str, BaseModule] = {}
        self.session_factory = async_session_factory

    async def discover(self):
        eps = entry_points(group="demon_cry.modules")
        async with self.session_factory() as session:
            repo = ModuleRepository(session=session)
            for ep in eps:
                try:
                    module_class = ep.load()
                    instance = module_class()
                    self.modules[instance.name] = instance
                    logger.info("Registered module: %s", instance.name)
                    existing = await repo.get(module_name=instance.name)
                    if not existing:
                        defaults = instance.config_model().model_dump()
                        await repo.create(
                            module_name=instance.name, config=defaults, enabled=False
                        )
                except Exception:
                    logger.exception("Failed to load module: %s", ep.name)

    async def get_tools_schema(self) -> list[ToolDefinition]:
        tools: list[ToolDefinition] = []
        for module in self.modules.values():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": module.name,
                        "description": f"[Category: {module.category}] {module.description}",
                        "parameters": module.parameters_model.model_json_schema(),
                    },
                }
            )
        return tools

    async def execute(self, tool_name: str, **kwargs) -> dict:
        if tool_name not in self.modules:
            return {"error": f"Unknown module: {tool_name}"}
        try:
            module = self.modules[tool_name]
            config_data = await self._load_config(tool_name)
            config = module.config_model(**config_data)
            params = module.parameters_model(**kwargs)
            return await module.execute(config=config, params=params)
        except Exception as e:
            logger.exception("Error during execution of %s", tool_name)
            return {"error": str(e)}

    async def _load_config(self, module_name: str) -> dict:
        async with self.session_factory() as session:
            repo = ModuleRepository(session=session)
            record = await repo.get(module_name=module_name)
            if record and record.enabled:
                return record.config
        return {}
