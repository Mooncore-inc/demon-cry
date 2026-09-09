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

from demon_cry.core.module_registry import ModuleRegistry

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are Demon Cry — an autonomous OSINT investigation agent.
Your mission: gather, analyze, and synthesize information from PUBLIC sources.

## Investigation Strategy

1. **Decompose**: Break the query into sub-questions
2. **Plan**: Choose appropriate tools based on their descriptions
3. **Execute**: Call multiple independent tools in parallel when possible
4. **Verify**: Cross-reference facts from multiple sources
5. **Synthesize**: Combine findings into a coherent report
6. **Assess**: Rate confidence (High/Medium/Low) for each claim

## Tool Usage Principles

- Check tool's Category before calling — it defines the information boundary
- Call independent tools in parallel (e.g., multiple searches, multiple page parses)
- Chain tools when output of one is input for another (search → parse)
- If a tool fails or returns nothing, try alternative approaches
- NEVER fabricate data — if unsure, say so

## Advanced Search Tactics

- Use `category="files"` and `query="target filetype:pdf"` to find leaked documents or reports.
- Use `category="social media"` and `time_range="month"` to find recent activity of a person.
- Use `category="it"` for technical queries, GitHub repositories, or server configurations.
- If general search fails, switch to a specific category before giving up.

## Final Report Format

### Summary
[2-3 sentence overview]

### Key Findings
- **Finding 1**: [fact] (Source: [URL], Confidence: High/Medium/Low)

### Analysis
[Synthesis, patterns, contradictions]

### Limitations
[What couldn't be verified, missing data]

## Ethical Boundaries

✅ ALLOWED: Public profiles, company sites, registries (WHOIS/DNS), news, papers
❌ PROHIBITED: Private data, doxing, bypassing auth, illegal content

## Token Efficiency

- Be concise in tool calls — don't repeat the same queries
- Stop early if you have enough information for a confident report
- Use parallel tool calls when possible
- Don't over-explain in intermediate steps
- When tools are unavailable, compile all findings into a structured final report. Do not attempt to call tools — output only text with the investigation results, including sources and limitations"""

DEFAULT_ITERATION_LIMIT = 150


class TokenUsage(BaseModel):
    total: int = 0
    prompt: int = 0
    completion: int = 0
    reasoning: int = 0
    cache_hit: int = 0
    cache_miss: int = 0

    def __add__(self, other):
        return TokenUsage(
            total=self.total + other.total,
            prompt=self.prompt + other.prompt,
            completion=self.completion + other.completion,
            reasoning=self.reasoning + other.reasoning,
            cache_hit=self.cache_hit + other.cache_hit,
            cache_miss=self.cache_miss + other.cache_miss,
        )

    @classmethod
    def from_usage(cls, usage) -> "TokenUsage":
        details = getattr(usage, "completion_tokens_details", None)
        return cls(
            total=usage.total_tokens,
            prompt=usage.prompt_tokens,
            completion=usage.completion_tokens,
            reasoning=getattr(details, "reasoning_tokens", 0),
            cache_hit=getattr(usage, "prompt_cache_hit_tokens", 0),
            cache_miss=getattr(usage, "prompt_cache_miss_tokens", 0),
        )


class ToolCall(BaseModel):
    name: str
    arguments: dict = {}
    result: Any = None
    status: str = "success"


class ToolUsage(BaseModel):
    calls: list[ToolCall] = []

    def __add__(self, other):
        return ToolUsage(calls=self.calls + other.calls)

    def append(self, call: ToolCall):
        self.calls.append(call)

    def add_from_tool_call(self, tc, result) -> ToolCall:
        args = json.loads(tc.function.arguments)
        is_error = isinstance(result, dict) and "error" in result
        call = ToolCall(
            name=tc.function.name,
            arguments=args,
            result=result,
            status="error" if is_error else "success",
        )
        self.calls.append(call)
        return call


class LLM:
    """Asynchronous client for working with a Large Language Model.

    Manages the interaction loop with the LLM, including sending queries,
    processing tool calls, and tracking token usage.

    Attributes:
        client: Asynchronous OpenAI-compatible API client.
        model: Identifier of the model being used.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        registry: ModuleRegistry,
        system_prompt: str,
        iteration_limit: int,
    ):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.registry = registry
        self.system_prompt = system_prompt
        self.iteration_limit = iteration_limit

    async def run_chain(
        self, user_query: str
    ) -> tuple[str | None, ToolUsage, TokenUsage]:
        """Оркестратор: управляет циклом взаимодействия с LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]
        tools_list = await self.registry.get_tools_schema()
        tools_used = ToolUsage()
        tokens = TokenUsage()

        for i in range(self.iteration_limit):
            tool_choice = "none" if i == self.iteration_limit - 1 else "auto"

            response_message, usage = await self._call_llm(
                messages=messages, tools_list=tools_list, tool_choice=tool_choice
            )

            tokens += TokenUsage.from_usage(usage)

            if not response_message.tool_calls:
                return response_message.content, tools_used, tokens

            messages.append(response_message)
            await self._process_tool_calls(
                response_message.tool_calls, messages, tools_used
            )

        return None, tools_used, tokens

    async def _call_llm(
        self,
        messages: list[dict],
        tools_list: list[dict],
        tool_choice: str,
        temperature: float = 0.3,
    ) -> tuple[Any, Any]:
        """Выполняет запрос к модели."""
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            tools=tools_list,
            tool_choice=tool_choice,
        )

        logger.info("Tokens used: %s", completion.usage)
        return completion.choices[0].message, completion.usage

    async def _process_tool_calls(
        self, tool_calls: list, messages: list[dict], tools_used: ToolUsage
    ):
        """Обрабатывает вызовы инструментов и добавляет результаты в историю."""

        async def execute_single(tool_call):
            logger.info("Tool call: %s", tool_call.function.name)

            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = await self.registry.execute(name, **args)

            tools_used.add_from_tool_call(tool_call, result)

            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            }

        results = await asyncio.gather(*(execute_single(tc) for tc in tool_calls))
        messages.extend(results)
