import logging

from fastapi import APIRouter, Depends
from pathlib import Path
from pydantic import BaseModel

from core.auth import verify_master_key
from core.llm import LLM, TokenUsage

router = APIRouter()

logger = logging.getLogger(__name__)

class OSINTRequest(BaseModel):
    target: str

class OSINTResponse(BaseModel):
    status: str
    result: str
    tools_used: list[dict] = []
    tokens: TokenUsage = TokenUsage()

PROMPTS_DIR = Path(__file__).parent / ".." / "prompts"
system_prompt_template = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")

from core.config import config
from core.module_registry import registry

llm = LLM(config=config,registry=registry,system_prompt=system_prompt_template)

@router.post(path="/investigate", dependencies=[Depends(verify_master_key)])
async def investigate(req: OSINTRequest):
    try:
        res, tools, tokens = await llm.run_chain(
            user_query=req.target
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
