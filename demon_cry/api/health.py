import time
import logging
import httpx

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from demon_cry.config import Config
from demon_cry.utils.dependencies import get_config

router = APIRouter()

logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    latency_ms: int

@router.get("/health")
async def health(config: Config = Depends(get_config)):
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            await client.head(config.base_url)
        latency_ms = round((time.perf_counter() - start) * 1000)
        return HealthResponse(status="ok", latency_ms=latency_ms)
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000)
        logger.error("health err: %s", e)
        return HealthResponse(status="error", latency_ms=latency_ms)
