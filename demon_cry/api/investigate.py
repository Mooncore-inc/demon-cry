import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from demon_cry.api.dependencies import CurrentUser, LLMRepo, AppRegistry, SettingsRepo
from demon_cry.services.llm import LLM, TokenUsage, ToolUsage, DEFAULT_SYSTEM_PROMPT, DEFAULT_ITERATION_LIMIT

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
    registry: AppRegistry,
    llm_repo: LLMRepo,
    set_repo: SettingsRepo,
    user: CurrentUser,
    ):
    try:
        if req.llm_model_id:
            model = await llm_repo.get_by_id(req.llm_model_id)
        else:
            model = await llm_repo.get(is_default=True)
        if not model:
            raise HTTPException(status_code=404, detail="LLM model not found")

        # Fetch settings from DB
        system_prompt_row = await set_repo.get(key="system_prompt")
        iteration_limit_row = await set_repo.get(key="iteration_limit")

        system_prompt = system_prompt_row.value if system_prompt_row else DEFAULT_SYSTEM_PROMPT
        iteration_limit = int(iteration_limit_row.value) if iteration_limit_row else DEFAULT_ITERATION_LIMIT

        llm = LLM(
            base_url=model.base_url,
            api_key=model.api_key,
            model=model.model_name,
            registry=registry,
            system_prompt=system_prompt,
            iteration_limit=iteration_limit,
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
