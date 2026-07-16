import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from core.config import config
from core.module_registry import registry

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
system_prompt_template = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")

class LLM:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self.model = config.model

    def _render_prompt(self, tokens_remaining: int, status: str) -> str:
        budget = f"TOKEN BUDGET:\nRemaining: {tokens_remaining} tokens. Status: {status}."
        if status == "critical":
            budget += "\nSTOP using tools. Generate a final summary report with all findings now."
        else:
            budget += "\nContinue working as usual."
        return system_prompt_template.replace("{{token_budget}}", budget)

    async def run_chain(self, user_query: str, max_tokens: int = 10000) -> tuple[str | None, list[dict], int]:
        """Оркестратор: управляет циклом взаимодействия с LLM."""
        threshold = int(max_tokens * 0.2)
        messages = [
            {"role": "system", "content": self._render_prompt(max_tokens, "normal")},
            {"role": "user", "content": user_query}
            ]
        tools_used: list[dict] = []
        total_tokens_used = 0

        while total_tokens_used < max_tokens:
            tokens_remaining = max_tokens - total_tokens_used
            status = "critical" if tokens_remaining < threshold else "normal"
            messages[0]["content"] = self._render_prompt(tokens_remaining, status)

            response_message, usage = await self._call_llm(messages)
            total_tokens_used += usage.total_tokens

            if not response_message.tool_calls:
                return response_message.content, tools_used, total_tokens_used

            for tc in response_message.tool_calls:
                tools_used.append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

            messages.append(response_message)
            await self._process_tool_calls(response_message.tool_calls, messages)

        logger.warning(f"Token limit exceeded ({max_tokens})")
        return None, tools_used, total_tokens_used

    async def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> tuple[Any, Any]:
        """Выполняет запрос к модели."""
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            tools=await registry.get_tools_schema(),
            tool_choice="auto"
        )
        logger.info(f"Tokens used: {completion.usage}")
        return completion.choices[0].message, completion.usage

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
