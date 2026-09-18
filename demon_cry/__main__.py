import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import add_scalar_reference

from demon_cry.api import router
from demon_cry.core.plugin_registry import PluginRegistry
from demon_cry.utils import version

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    plugins = PluginRegistry()
    await plugins.discover()
    app.state.registry = plugins
    yield


app = FastAPI(title="demon cry core", version=version.get_version(), lifespan=lifespan)

app.include_router(router)
add_scalar_reference(app)
