from fastapi import APIRouter

from demon_cry.api import health, investigate, tools
from demon_cry.api.admin import admin_router

router = APIRouter(prefix="/api")

router.include_router(health.router, tags=["System"])
router.include_router(investigate.router, tags=["Investigation"])
router.include_router(tools.router, tags=["Tools"])

router.include_router(admin_router)
