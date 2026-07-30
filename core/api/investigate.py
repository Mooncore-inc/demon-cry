import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.auth import verify_master_key
from core.llm import llm

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str

class OSINTResponse(BaseModel):
    status: str
    result: str
    tools_used: list[dict] = []
    total_tokens: int = 0

@router.post(path="/investigate", dependencies=[Depends(verify_master_key)])
async def investigate(req: OSINTRequest):
    try:
        res, tools, tokens = await llm.run_chain(
            user_query=req.target
        )
        return OSINTResponse(status="success", result=res, tools_used=tools, total_tokens=tokens)
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return OSINTResponse(status="error", result="ошибка")
