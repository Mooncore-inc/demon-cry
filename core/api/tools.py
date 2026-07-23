import logging

from fastapi import APIRouter
from pydantic import BaseModel

from core.module_registry import registry

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str
    max_tokens: int = 15000

class OSINTResponse(BaseModel):
    status: str
    result: str | None = None
    tools_used: list[dict] = []
    total_tokens: int = 0

@router.get(path="/tools")
async def tools():
    return await registry.get_tools_schema()
