import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.module_registry import registry
from core.api.router import router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await registry.discover()
    yield

app = FastAPI(
    title="Demon cry",
    version="0.4.1",
    lifespan=lifespan
)

app.include_router(router)