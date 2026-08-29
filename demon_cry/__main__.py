import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from demon_cry.utils import version
from demon_cry.module_registry import registry
from demon_cry.api.router import router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.modules_dir = "modules"
    await registry.discover()
    yield

app = FastAPI(
    title="demon cry core",
    version=version.get_version(),
    lifespan=lifespan
)

app.include_router(router)
