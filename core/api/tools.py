import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from core.module_registry import registry

router = APIRouter()

logger = logging.getLogger(__name__)


class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolDefinition(BaseModel):
    type: str
    function: ToolFunction


class ToolsResponse(BaseModel):
    tools: list[ToolDefinition]


@router.get(path="/tools")
async def tools():
    tools = await registry.get_tools_schema()
    return ToolsResponse(tools=tools)
