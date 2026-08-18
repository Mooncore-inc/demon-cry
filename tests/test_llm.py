import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from demon_cry.llm import LLM, ToolUsage


# --- Mock helpers for OpenAI response objects ---

@dataclass
class MockReasoningTokens:
    reasoning_tokens: int = 0


@dataclass
class MockCompletionTokensDetails:
    reasoning_tokens: int = 0


@dataclass
class MockUsage:
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    completion_tokens_details: MockCompletionTokensDetails | None = None
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0


@dataclass
class MockFunction:
    name: str = ""
    arguments: str = "{}"


@dataclass
class MockToolCall:
    id: str = "call_123"
    function: MockFunction = None

    def __init__(self, id: str, name: str, arguments: dict):
        self.id = id
        self.function = MockFunction(name=name, arguments=json.dumps(arguments))


@dataclass
class MockMessage:
    content: str | None = None
    tool_calls: list[MockToolCall] | None = None


@dataclass
class MockChoice:
    message: MockMessage = None


@dataclass
class MockResponse:
    choices: list[MockChoice] = None
    usage: MockUsage = None


# --- Fixtures ---

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.base_url = "http://localhost:8000"
    config.api_key = "test-key"  # pragma: allowlist secret
    config.model = "test-model"
    config.iteration_limit = 5
    return config


@pytest.fixture
def mock_registry():
    registry = AsyncMock()
    registry.get_tools_schema = AsyncMock(return_value=[])
    registry.execute = AsyncMock(return_value={"status": "ok"})
    return registry


@pytest.fixture
def llm(mock_config, mock_registry):
    return LLM(config=mock_config, registry=mock_registry, system_prompt="You are a test.")


def make_usage(total=10, prompt=5, completion=5, reasoning=0, cache_hit=0, cache_miss=0):
    return MockUsage(
        total_tokens=total,
        prompt_tokens=prompt,
        completion_tokens=completion,
        completion_tokens_details=MockCompletionTokensDetails(reasoning_tokens=reasoning),
        prompt_cache_hit_tokens=cache_hit,
        prompt_cache_miss_tokens=cache_miss,
    )


# --- Edge case helpers ---

def make_tool_call_raw(id: str, name: str, raw_arguments: str) -> MockToolCall:
    tc = MockToolCall.__new__(MockToolCall)
    tc.id = id
    tc.function = MockFunction(name=name, arguments=raw_arguments)
    return tc


# --- Tests ---

@pytest.mark.asyncio
async def test_run_chain_no_tools(llm, mock_registry):
    mock_registry.get_tools_schema.return_value = []

    message = MockMessage(content="Hello, world!", tool_calls=None)
    usage = make_usage(total=20, prompt=10, completion=10)
    response = MockResponse(choices=[MockChoice(message=message)], usage=usage)

    llm.client.chat.completions.create = AsyncMock(return_value=response)

    content, tools_used, tokens = await llm.run_chain(user_query="test query")

    assert content == "Hello, world!"
    assert tools_used.calls == []
    assert tokens.total == 20
    assert tokens.prompt == 10
    assert tokens.completion == 10
    llm.client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_run_chain_with_tools(llm, mock_registry):
    mock_registry.get_tools_schema.return_value = [
        {"type": "function", "function": {"name": "test_tool", "description": "desc", "parameters": {}}}
    ]

    tool_call = MockToolCall(id="call_1", name="test_tool", arguments={"query": "test"})
    first_msg = MockMessage(content=None, tool_calls=[tool_call])
    first_usage = make_usage(total=15, prompt=8, completion=7)

    second_msg = MockMessage(content="Result is done", tool_calls=None)
    second_usage = make_usage(total=10, prompt=5, completion=5)

    llm.client.chat.completions.create = AsyncMock(side_effect=[
        MockResponse(choices=[MockChoice(message=first_msg)], usage=first_usage),
        MockResponse(choices=[MockChoice(message=second_msg)], usage=second_usage),
    ])

    content, tools_used, tokens = await llm.run_chain(user_query="test query")

    assert content == "Result is done"
    assert len(tools_used.calls) == 1
    assert tools_used.calls[0].name == "test_tool"
    assert tools_used.calls[0].arguments == {"query": "test"}
    assert tokens.total == 25
    assert tokens.prompt == 13
    assert tokens.completion == 12
    mock_registry.execute.assert_called_once_with("test_tool", query="test")


@pytest.mark.asyncio
async def test_process_tool_calls(llm, mock_registry):
    messages = [{"role": "user", "content": "hello"}]

    tc1 = MockToolCall(id="call_1", name="tool_a", arguments={"x": 1})
    tc2 = MockToolCall(id="call_2", name="tool_b", arguments={"y": 2})

    tools_used = ToolUsage()
    await llm._process_tool_calls([tc1, tc2], messages, tools_used)

    assert len(messages) == 3
    assert messages[1]["role"] == "tool"
    assert messages[1]["tool_call_id"] == "call_1"
    assert json.loads(messages[1]["content"]) == {"status": "ok"}
    assert messages[2]["role"] == "tool"
    assert messages[2]["tool_call_id"] == "call_2"
    assert mock_registry.execute.call_count == 2


# --- Edge case tests ---

@pytest.mark.asyncio
async def test_run_chain_invalid_json_in_tool_call(llm, mock_registry):
    mock_registry.get_tools_schema.return_value = [
        {"type": "function", "function": {"name": "test_tool", "description": "desc", "parameters": {}}}
    ]

    bad_tc = make_tool_call_raw(id="call_1", name="test_tool", raw_arguments="{invalid json!!!")
    first_msg = MockMessage(content=None, tool_calls=[bad_tc])
    first_usage = make_usage(total=10, prompt=5, completion=5)

    llm.client.chat.completions.create = AsyncMock(
        return_value=MockResponse(choices=[MockChoice(message=first_msg)], usage=first_usage)
    )

    with pytest.raises(json.JSONDecodeError):
        await llm.run_chain(user_query="test query")


@pytest.mark.asyncio
async def test_process_tool_calls_invalid_json(llm, mock_registry):
    messages = [{"role": "user", "content": "hello"}]
    bad_tc = make_tool_call_raw(id="call_1", name="tool_a", raw_arguments="not json")

    with pytest.raises(json.JSONDecodeError):
        await llm._process_tool_calls([bad_tc], messages, ToolUsage())


@pytest.mark.asyncio
async def test_run_chain_registry_error(llm, mock_registry):
    mock_registry.get_tools_schema.return_value = [
        {"type": "function", "function": {"name": "test_tool", "description": "desc", "parameters": {}}}
    ]
    mock_registry.execute.return_value = {"error": "Unknown module: test_tool"}

    tool_call = MockToolCall(id="call_1", name="test_tool", arguments={"query": "test"})
    first_msg = MockMessage(content=None, tool_calls=[tool_call])
    first_usage = make_usage(total=15, prompt=8, completion=7)

    second_msg = MockMessage(content="Done", tool_calls=None)
    second_usage = make_usage(total=10, prompt=5, completion=5)

    llm.client.chat.completions.create = AsyncMock(side_effect=[
        MockResponse(choices=[MockChoice(message=first_msg)], usage=first_usage),
        MockResponse(choices=[MockChoice(message=second_msg)], usage=second_usage),
    ])

    content, tools_used, tokens = await llm.run_chain(user_query="test query")

    assert content == "Done"
    assert len(tools_used.calls) == 1
    assert tools_used.calls[0].name == "test_tool"
    mock_registry.execute.assert_called_once()


@pytest.mark.asyncio
async def test_run_chain_iteration_limit(mock_registry):
    config = MagicMock()
    config.base_url = "http://localhost:8000"
    config.api_key = "test-key"  # pragma: allowlist secret
    config.model = "test-model"
    config.iteration_limit = 2

    llm = LLM(config=config, registry=mock_registry, system_prompt="test")
    mock_registry.get_tools_schema.return_value = [
        {"type": "function", "function": {"name": "tool", "description": "d", "parameters": {}}}
    ]

    tool_call = MockToolCall(id="call_1", name="tool", arguments={"x": 1})
    tool_msg = MockMessage(content=None, tool_calls=[tool_call])
    usage = make_usage(total=10, prompt=5, completion=5)

    llm.client.chat.completions.create = AsyncMock(
        return_value=MockResponse(choices=[MockChoice(message=tool_msg)], usage=usage)
    )

    result = await llm.run_chain(user_query="test")

    content, tools_used, tokens = result
    assert content is None
    assert len(tools_used.calls) == 2
    assert tokens.total == 20
    assert llm.client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_run_chain_empty_response(llm, mock_registry):
    mock_registry.get_tools_schema.return_value = []

    message = MockMessage(content=None, tool_calls=None)
    usage = make_usage(total=5, prompt=3, completion=2)
    response = MockResponse(choices=[MockChoice(message=message)], usage=usage)

    llm.client.chat.completions.create = AsyncMock(return_value=response)

    content, tools_used, tokens = await llm.run_chain(user_query="test")

    assert content is None
    assert tools_used.calls == []
    assert tokens.total == 5
