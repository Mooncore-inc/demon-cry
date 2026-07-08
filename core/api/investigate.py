import logging

from fastapi import APIRouter
from pydantic import BaseModel

from core.llm import llm

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str
    max_iterations: int = 10

class OSINTResponse(BaseModel):
    status: str
    result: str | None = None

@router.post(path="/investigate")
async def investigate(req: OSINTRequest):
    try:
        res = await llm.run_chain(
            user_query=req.target,
            max_iterations=req.max_iterations
        )
        return OSINTResponse(status="success", result=res)
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return OSINTResponse(status="error", result="ошибка")
