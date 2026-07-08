import json
import logging
from typing import Any

from openai import OpenAI
from core.config import config
from core.module_registry import registry

logger = logging.getLogger(__name__)

system_prompt = """Ты Demon Cry — OSINT-агент для работы с ПУБЛИЧНЫМИ данными.

ПРАВИЛА:
1. Работай ТОЛЬКО с открытыми источниками (сайты, публичные реестры, соцсети)
2. НЕ собирай приватную информацию (пароли, личные данные без согласия)
3. Если запрос легитимный (поиск публичной инфо) — выполняй
4. Отказывайся ТОЛЬКО если запрос явно незаконный

Легитимные запросы:
- Поиск публичных профилей
- Анализ сайтов компаний/учебных заведений
- Проверка доменов, IP
- Поиск упоминаний в открытых источниках
"""

class LLM:
    def __init__(self):
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self.model = config.model

    def run_chain(self, user_query: str, max_iterations: int = 10) -> str | None:
        """Оркестратор: управляет циклом взаимодействия с LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
            ]

        for _ in range(max_iterations):
            response_message = self._call_llm(messages)

            if not response_message.tool_calls:
                return response_message.content

            messages.append(response_message)
            self._process_tool_calls(response_message.tool_calls, messages)

        logger.warning(f"Iteration limit exceeded ({max_iterations})")
        return None

    def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> Any:
        """Выполняет запрос к модели."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            tools=registry.get_tools_schema(),
            tool_choice="auto"
        )
        logger.info(f"Tokens used: {completion.usage}")
        return completion.choices[0].message

    def _process_tool_calls(self, tool_calls: list, messages: list[dict]):
        """Обрабатывает вызовы инструментов и добавляет результаты в историю."""
        for tool_call in tool_calls:
            logger.info(f"Tool call: {tool_call.function.name}")
            result = self._execute_tool(tool_call)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

    def _execute_tool(self, tool_call) -> dict:
        """Парсит аргументы и выполняет инструмент."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
            
            if name not in registry.modules:
                return {"error": f"Tool '{name}' not found"}
                
            return registry.execute(name, **args)
        except Exception as e:
            logger.exception(f"Error during tool execution {name}")
            return {"error": str(e)}

llm = LLM()