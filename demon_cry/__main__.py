import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from demon_cry.utils import version
from demon_cry.core.module_registry import ModuleRegistry
from demon_cry.api import router
from demon_cry.core.config import init_defaults

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    modules = ModuleRegistry()
    await modules.discover()
    app.state.registry = modules
    await init_defaults()
    yield

app = FastAPI(
    title="demon cry core",
    version=version.get_version(),
    lifespan=lifespan
)

app.include_router(router)
