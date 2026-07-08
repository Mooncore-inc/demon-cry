import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.module_registry import registry

from modules.web_search import WebSearch
from modules.parse_website import ParseWebsite

from core.api import investigate, health

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await registry.register(WebSearch())
    await registry.register(ParseWebsite())
    yield

app = FastAPI(
    title="Demon cry",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(investigate.router)
app.include_router(health.router)
