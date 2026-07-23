import logging

from fastapi import APIRouter
from pydantic import BaseModel

from core.llm import llm

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

@router.post(path="/investigate")
async def investigate(req: OSINTRequest):
    try:
        res, tools, tokens = await llm.run_chain(
            user_query=req.target,
            max_tokens=req.max_tokens
        )
        return OSINTResponse(status="success", result=res, tools_used=tools, total_tokens=tokens)
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return OSINTResponse(status="error", result="ошибка")
