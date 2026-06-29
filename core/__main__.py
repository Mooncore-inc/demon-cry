import logging

from fastapi import FastAPI

from core.module_registry import registry

from modules.web_search import WebSearch
from modules.parse_website import ParseWebsite

from core.api import investigate

logger = logging.getLogger(__name__)

registry.register(WebSearch())
registry.register(ParseWebsite())

app = FastAPI(
    title="Demon cry",
    version="0.1.0"
)

app.include_router(investigate.router)
