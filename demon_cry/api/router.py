from fastapi import APIRouter

from demon_cry.api import (
    investigate,
    health,
    tools
)

router = APIRouter(prefix="/api")

router.include_router(health.router, tags=["System"])
router.include_router(investigate.router, tags=["Investigation"])
router.include_router(tools.router, tags=["Tools"])
