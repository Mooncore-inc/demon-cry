import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from demon_cry.api.dependencies import CurrentUser, LLMRepo, AppConfig, AppRegistry
from demon_cry.services.llm import LLM, TokenUsage, ToolUsage

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str
    llm_model_id: int | None = None

class OSINTResponse(BaseModel):
    status: str
    result: str
    tools_used: ToolUsage = ToolUsage()
    tokens: TokenUsage = TokenUsage()

@router.post(path="/investigate")
async def investigate(
    req: OSINTRequest,
    config: AppConfig,
    registry: AppRegistry,
    llm_repo: LLMRepo,
    user: CurrentUser,
    ):
    try:
        if req.llm_model_id:
            model = await llm_repo.get_by_id(req.llm_model_id)
        else:
            model = await llm_repo.get(is_default=True)
        if not model:
            raise HTTPException(status_code=404, detail="LLM model not found")

        llm = LLM(
            base_url=model.base_url,
            api_key=model.api_key,
            model=model.model_name,
            config=config,
            registry=registry,
            system_prompt=config.system_prompt,
        )

        res, tools, tokens = await llm.run_chain(user_query=req.target)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Investigation failed: %s", e)
        return OSINTResponse(status="error", result="ошибка")
