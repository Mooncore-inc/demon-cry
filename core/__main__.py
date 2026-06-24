import logging

from core.module_registry import registry
from core.llm import llm

from modules.web_search import WebSearch
from modules.parse_website import ParseWebsite

logger = logging.getLogger(__name__)

registry.register(WebSearch())
registry.register(ParseWebsite())

print(llm.run_chain("кто такой fazzyt?"))
