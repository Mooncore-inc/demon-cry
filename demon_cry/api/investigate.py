import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from demon_cry.api.auth import get_current_user
from demon_cry.llm import TokenUsage, ToolUsage
from demon_cry.api.dependencies import get_llm
from demon_cry.database.models.users import UserModel

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
    llm = Depends(get_llm),
    user: UserModel = Depends(get_current_user),
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
