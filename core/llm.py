"""Module for interacting with a Large Language Model (LLM).

Provides an asynchronous client for sending queries to an LLM,
processing tool calls, and managing the dialogue loop
using an OpenAI-compatible API.
"""

import asyncio
import json
import logging
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from core.config import Config
from core.module_registry import ModuleRegistry

logger = logging.getLogger(__name__)

class TokenUsage(BaseModel):
    total: int = 0
    prompt: int = 0
    completion: int = 0
    reasoning: int = 0
    cache_hit: int = 0
    cache_miss: int = 0

    def __add__(self, other):
        return TokenUsage(
            total = self.total + other.total,
            prompt = self.prompt + other.prompt,
            completion = self.completion + other.completion,
            reasoning = self.reasoning + other.reasoning,
            cache_hit = self.cache_hit + other.cache_hit,
            cache_miss = self.cache_miss + other.cache_miss,
        )

    @classmethod
    def from_usage(cls, usage) -> "TokenUsage":
        details = getattr(usage, "completion_tokens_details", None)
        return cls(
            total = usage.total_tokens,
            prompt = usage.prompt_tokens,
            completion = usage.completion_tokens,
            reasoning = getattr(details, "reasoning_tokens", 0),
            cache_hit = getattr(usage, 'prompt_cache_hit_tokens', 0),
            cache_miss = getattr(usage, 'prompt_cache_miss_tokens', 0),
        )


class LLM:
    """Asynchronous client for working with a Large Language Model.

    Manages the interaction loop with the LLM, including sending queries,
    processing tool calls, and tracking token usage.

    Attributes:
        client: Asynchronous OpenAI-compatible API client.
        model: Identifier of the model being used.
    """

    def __init__(self, config: Config, registry: ModuleRegistry, system_prompt: str):
        self.client = AsyncOpenAI(
            base_url = config.base_url,
            api_key = config.api_key
        )
        self.model = config.model
        self.config = config
        self.registry = registry
        self.system_prompt = system_prompt

    async def run_chain(self, user_query: str) -> tuple[str | None, list[dict], TokenUsage]:
        """Оркестратор: управляет циклом взаимодействия с LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
            ]
        tools_list = await self.registry.get_tools_schema()
        tools_used: list[dict] = []
        tokens = TokenUsage()

        for i in range(self.config.iteration_limit):
            tool_choice = "none" if i == self.config.iteration_limit - 1 else "auto"

            response_message, usage = await self._call_llm(messages=messages, tools_list=tools_list, tool_choice=tool_choice)

            tokens += TokenUsage.from_usage(usage)

            if not response_message.tool_calls:
                return response_message.content, tools_used, tokens

            for tc in response_message.tool_calls:
                tools_used.append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

            messages.append(response_message)
            await self._process_tool_calls(response_message.tool_calls, messages)

    async def _call_llm(
            self,
            messages: list[dict],
            tools_list: list[dict],
            tool_choice: str,
            temperature: float = 0.3
        ) -> tuple[Any, Any]:
        """Выполняет запрос к модели."""
        completion = await self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = temperature,
            tools = tools_list,
            tool_choice = tool_choice,
        )

        logger.info("Tokens used: %s", completion.usage)
        return completion.choices[0].message, completion.usage

    async def _process_tool_calls(self, tool_calls: list, messages: list[dict]):
        """Обрабатывает вызовы инструментов и добавляет результаты в историю."""

        async def execute_single(tool_call):
            logger.info("Tool call: %s", tool_call.function.name)

            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = await self.registry.execute(name, **args)

            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            }

        results = await asyncio.gather(*(execute_single(tc) for tc in tool_calls))
        messages.extend(results)
