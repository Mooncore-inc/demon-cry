import json
import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Dict, TypedDict

from demon_cry_base import BaseModule


class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolDefinition(TypedDict):
    type: str
    function: ToolFunction

logger = logging.getLogger(__name__)


class ModuleRegistry:
    def __init__(self, modules_dir: str = "modules"):
        self.modules: Dict[str, BaseModule] = {}
        self.modules_dir = modules_dir

    async def register(self, module: BaseModule):
        self.modules[module.name] = module
        logger.info("Registered module: %s", module.name)

    async def discover(self):
        eps = entry_points(group="demon_cry.modules")
        for ep in eps:
            try:
                module_class = ep.load()
                instance = module_class()
                await self.register(instance)
            except Exception:
                logger.exception("Failed to load module: %s", ep.name)

    async def get_tools_schema(self) -> list[ToolDefinition]:
        tools: list[ToolDefinition] = []
        for module in self.modules.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": module.name,
                    "description": f"[Category: {module.category}] {module.description}",
                    "parameters": module.parameters
                }
            })
        return tools

    async def execute(self, tool_name: str, **kwargs) -> dict:
        if tool_name not in self.modules:
            return {"error": f"Unknown module: {tool_name}"}
        try:
            config = self._load_config(tool_name)
            return await self.modules[tool_name].execute(config=config, **kwargs)
        except Exception as e:
            logger.exception("Error during execution of %s", tool_name)
            return {"error": str(e)}

    def _load_config(self, module_name: str) -> dict:
        config_path = Path(self.modules_dir) / module_name / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        return {}


registry = ModuleRegistry()
