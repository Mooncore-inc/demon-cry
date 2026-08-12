import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.auth import verify_master_key
from core.llm import TokenUsage
from core.dependencies import get_llm

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str

class OSINTResponse(BaseModel):
    status: str
    result: str
    tools_used: list[dict] = []
    tokens: TokenUsage = TokenUsage()

@router.post(path="/investigate", dependencies=[Depends(verify_master_key)])
async def investigate(
    req: OSINTRequest,
    llm = Depends(get_llm)
    ):
    try:
        res, tools, tokens = await llm.run_chain(
            user_query=req.target
        )
        if res is None:
            return OSINTResponse(
                status="error",
                result="Модель не завершила работу за отведённые итерации",
                tools_used=tools,
                tokens=tokens,
            )
        return OSINTResponse(
            status="success",
            result=res,
            tools_used=tools,
            tokens=tokens,
        )
    except Exception as e:
        logger.error("Investigation failed: %s", e)
        return OSINTResponse(status="error", result="ошибка")
