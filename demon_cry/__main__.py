import logging
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI

from demon_cry.module_registry import registry
from demon_cry.api.router import router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.modules_dir = "modules"
    await registry.discover()
    yield

try:
    _version = version("demon-cry")
except PackageNotFoundError:
    _version = "0.0.0"

app = FastAPI(
    title="Demon cry",
    version=_version,
    lifespan=lifespan
)

app.include_router(router)
