import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from core.config import config
from core.module_registry import registry

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
system_prompt = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")

class LLM:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self.model = config.model

    async def run_chain(self, user_query: str, max_iterations: int = 10) -> tuple[str | None, list[dict]]:
        """Оркестратор: управляет циклом взаимодействия с LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
            ]
        tools_used: list[dict] = []

        for _ in range(max_iterations):
            response_message = await self._call_llm(messages)

            if not response_message.tool_calls:
                return response_message.content, tools_used

            for tc in response_message.tool_calls:
                tools_used.append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

            messages.append(response_message)
            await self._process_tool_calls(response_message.tool_calls, messages)

        logger.warning(f"Iteration limit exceeded ({max_iterations})")
        return None, tools_used

    async def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> Any:
        """Выполняет запрос к модели."""
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            tools=await registry.get_tools_schema(),
            tool_choice="auto"
        )
        logger.info(f"Tokens used: {completion.usage}")
        return completion.choices[0].message

    async def _process_tool_calls(self, tool_calls: list, messages: list[dict]):
        """Обрабатывает вызовы инструментов и добавляет результаты в историю."""
        for tool_call in tool_calls:
            logger.info(f"Tool call: {tool_call.function.name}")
            result = await self._execute_tool(tool_call)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

    async def _execute_tool(self, tool_call) -> dict:
        """Парсит аргументы и выполняет инструмент."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
            if name not in registry.modules:
                return {"error": f"Tool '{name}' not found"}
            return await registry.execute(name, **args)
        except Exception as e:
            logger.exception(f"Error during tool execution {name}")
            return {"error": str(e)}

llm = LLM()
