import logging

from typing import Dict, Type
from modules.base_modules import OSINTModule

logger = logging.getLogger(__name__)

class ModuleRegistry:
    def __init__(self):
        self.modules: Dict[str, OSINTModule] = {}
    
    def register(self, module: OSINTModule):
        """Регистрирует модуль"""
        self.modules[module.name] = module
        logger.info(f"Registered module: {module.name}")
    
    def get_tools_schema(self) -> list:
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
    
    def execute(self, tool_name: str, **kwargs) -> dict:
        """Выполняет модуль по имени"""
        if tool_name not in self.modules:
            return {"error": f"Unknown module: {tool_name}"}
        
        module = self.modules[tool_name]
        return module.execute(**kwargs)

registry = ModuleRegistry()