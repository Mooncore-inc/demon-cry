"""Базовые классы для OSINT-модулей."""
from typing import Protocol

class OSINTModule(Protocol):
    """Базовый класс для всех OSINT-модулей"""

    name: str
    description: str
    parameters: dict

    async def execute(self, **_kwargs) -> dict:
        """Логика выполнения"""
        return {}
