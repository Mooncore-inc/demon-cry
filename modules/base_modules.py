from abc import ABC, abstractmethod

class OSINTModule(ABC):
    """Базовый класс для всех OSINT-модулей"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя модуля"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema параметров"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Логика выполнения"""
        pass