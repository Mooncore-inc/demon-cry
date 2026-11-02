from fastapi import APIRouter

from demon_cry.api.investigate.crd import crd_router
from demon_cry.api.investigate.entities import entities_router
from demon_cry.api.investigate.graph import graph_router
from demon_cry.api.investigate.links import links_router
from demon_cry.api.investigate.tools import tools_router

router = APIRouter()

router.include_router(crd_router)
router.include_router(tools_router)
router.include_router(entities_router)
router.include_router(links_router)
router.include_router(graph_router)

__all__ = ["router"]
