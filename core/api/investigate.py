from fastapi import APIRouter
from pydantic import BaseModel

from core.llm import llm

router = APIRouter()

class OSINTRequest(BaseModel):
    target: str
    max_iterations: int = 10

@router.post(path="/investigate")
def investigate(req: OSINTRequest):

    res = llm.run_chain(
        user_query=req.target,
        max_iterations=req.max_iterations
    )

    return res