import logging

from fastapi import APIRouter
from pydantic import BaseModel

from demon_cry.api.dependencies import CurrentUser
from demon_cry.llm import TokenUsage, ToolUsage
from demon_cry.api.dependencies import AppLLM

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str

class OSINTResponse(BaseModel):
    status: str
    result: str
    tools_used: ToolUsage = ToolUsage()
    tokens: TokenUsage = TokenUsage()

@router.post(path="/investigate")
async def investigate(
    req: OSINTRequest,
    llm: AppLLM,
    user: CurrentUser,
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
