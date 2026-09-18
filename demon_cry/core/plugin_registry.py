import logging
from importlib.metadata import entry_points
from pkgutil import resolve_name
from typing import Any, TypedDict

from demon_cry_base import BasePlugin

from demon_cry.database.engine import async_session_factory
from demon_cry.database.repositories import PluginRepository


class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolDefinition(TypedDict):
    type: str
    function: ToolFunction


logger = logging.getLogger(__name__)


class PluginRegistry:
    def __init__(self):
        self.plugins: dict[str, BasePlugin] = {}
        self.session_factory = async_session_factory

    async def discover(self):
        eps = entry_points(group="demon_cry.plugins")
        async with self.session_factory() as session:
            repo = PluginRepository(session=session)
            for ep in eps:
                try:
                    plugin_class = ep.load()
                    instance = plugin_class()
                    self.plugins[instance.name] = instance
                    logger.info("Registered plugin: %s", instance.name)
                    existing = await repo.get(plugin_name=instance.name)
                    if not existing:
                        defaults = instance.config_model().model_dump()
                        await repo.create(
                            plugin_name=instance.name, config=defaults, enabled=False
                        )
                except Exception:
                    logger.exception("Failed to load plugin: %s", ep.name)

    async def get_tools_schema(self) -> list[ToolDefinition]:
        tools: list[ToolDefinition] = []
        for plugin in self.plugins.values():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": plugin.name,
                        "description": f"[Category: {plugin.category}] {plugin.description}",
                        "parameters": plugin.parameters_model.model_json_schema(),
                    },
                }
            )
        return tools

    async def execute(self, tool_name: str, **kwargs) -> dict:
        if tool_name not in self.plugins:
            return {"error": f"Unknown plugin: {tool_name}"}
        try:
            plugin = self.plugins[tool_name]
            config_data = await self._load_config(tool_name)
            config = plugin.config_model(**config_data)
            params = plugin.parameters_model(**kwargs)

            runner_func = resolve_name(plugin.execute_func)

            return await runner_func(config=config, params=params)

        except Exception as e:
            logger.exception("Error during execution of %s", tool_name)
            return {"error": str(e)}

    async def _load_config(self, plugin_name: str) -> dict:
        async with self.session_factory() as session:
            repo = PluginRepository(session=session)
            record = await repo.get(plugin_name=plugin_name)
            if record and record.enabled:
                return record.config
        return {}
