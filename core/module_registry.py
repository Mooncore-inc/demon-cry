import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Dict

import modules as modules_pkg
from modules.base_modules import OSINTModule

logger = logging.getLogger(__name__)

EXCLUDE = {"base_modules", "__init__"}

class ModuleRegistry:
    def __init__(self):
        self.modules: Dict[str, OSINTModule] = {}

    async def register(self, module: OSINTModule):
        """Регистрирует модуль"""
        self.modules[module.name] = module
        logger.info(f"Registered module: {module.name}")

    async def discover(self):
        """Автоматически находит и регистрирует все модули в папке modules/"""
        pkg_path = Path(modules_pkg.__file__).parent
        for _, module_name, _ in pkgutil.iter_modules([str(pkg_path)]):
            if module_name in EXCLUDE:
                continue
            try:
                mod = importlib.import_module(f"modules.{module_name}")
            except Exception:
                logger.exception(f"Failed to import modules.{module_name}")
                continue
            for obj in vars(mod).values():
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, OSINTModule)
                    and obj is not OSINTModule
                ):
                    try:
                        await self.register(obj())
                    except Exception:
                        logger.exception(f"Failed to instantiate {obj.__name__}")

    async def get_tools_schema(self) -> list:
        """Возвращает JSON Schema всех модулей для ИИ"""
        tools = []
        for module in self.modules.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": module.name,
                    "description": module.description,
                    "parameters": module.parameters
                }
            })
        return tools

    async def execute(self, tool_name: str, **kwargs) -> dict:
        """Выполняет модуль по имени"""
        if tool_name not in self.modules:
            return {"error": f"Unknown module: {tool_name}"}

        module = self.modules[tool_name]
        return await module.execute(**kwargs)

registry = ModuleRegistry()
